from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, date
import calendar
# from django.contrib.auth.decorators import login_required
from django.db.models import Q

from common.models import Appointment
from theme_name.models import PatientRegistration
from provider.models import Provider
from provider.forms import AppointmentForm
from .dashboard import get_provider

# @login_required
def provider_appointments(request):
    """Provider appointments view using Django ORM"""
    provider = get_provider(request)
    
    # Rest of your code remains the same...
    
    # When calculating appointment statistics, check if status field exists
    use_status_field = hasattr(Appointment, 'status')
    
    today_count = todays_appointments.count()
    
    if use_status_field:
        upcoming_count = appointments.filter(status='Scheduled').count()
        completed_count = appointments.filter(status='Completed').count()
        cancelled_count = appointments.filter(status='Cancelled').count()
    else:
        # Alternative counting logic if status field doesn't exist
        now = timezone.now()
        upcoming_count = appointments.filter(time__gt=now).count()
        completed_count = appointments.filter(time__lt=now).count()
        cancelled_count = 0  # Can't determine cancelled without status field
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'appointments': appointments,
        'todays_appointments': todays_appointments,
        'calendar_data': calendar_data,
        'view_type': view_type,
        'selected_date': selected_date,
        'date_display': date_display,
        'prev_date': prev_date,
        'next_date': next_date,
        'today_date': timezone.now().date().strftime('%Y-%m-%d'),
        'stats': {
            'today_count': today_count,
            'upcoming_count': upcoming_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count
        },
        'active_section': 'appointments'
    }
    
    return render(request, "provider/appointments.html", context)

def get_appointment_date(appointment):
    """Extract date from appointment time."""
    try:
        if hasattr(appointment, 'time') and appointment.time:
            # If appointment.time is a datetime object, return its date
            if hasattr(appointment.time, 'date'):
                return appointment.time.date()
            
        # For string representations (from older code)
        if isinstance(appointment, dict) and appointment.get('time'):
            time_str = appointment.get('time')
            if '-' in time_str:
                date_part = time_str.split('-')[0].strip()
                for fmt in ['%b %d, %Y', '%B %d, %Y']:
                    try:
                        from datetime import datetime
                        return datetime.strptime(date_part, fmt).date()
                    except ValueError:
                        continue
    except Exception:
        pass
    return None

def process_appointments_for_calendar(appointments, start_date, end_date, view_type):
    """Process appointments into a format suitable for calendar display"""
    result = {}
    
    if view_type == 'day':
        # For day view, organize by hour
        hours = []
        for hour in range(8, 18):  # 8 AM to 5 PM
            hour_start = start_date.replace(hour=hour, minute=0, second=0)
            hour_end = start_date.replace(hour=hour, minute=59, second=59)
            
            hour_appointments = appointments.filter(
                time__range=(hour_start, hour_end)
            )
            
            hours.append({
                'hour': f"{hour if hour <= 12 else hour-12}:00 {'AM' if hour < 12 else 'PM'}",
                'appointments': hour_appointments
            })
        
        result['hours'] = hours
        
    elif view_type == 'week':
        # For week view, organize by day of week
        days = []
        for day_offset in range(7):
            day_date = (start_date + timedelta(days=day_offset)).date()
            day_start = datetime.combine(day_date, datetime.min.time())
            day_end = datetime.combine(day_date, datetime.max.time())
            
            day_appointments = appointments.filter(
                time__range=(day_start, day_end)
            )
            
            days.append({
                'date': day_date,
                'day_name': day_date.strftime('%a'),
                'day_number': day_date.day,
                'is_today': day_date == timezone.now().date(),
                'appointments': day_appointments
            })
        
        result['days'] = days
        
        # Also organize by hour for the week grid
        time_slots = []
        for hour in range(8, 18):  # 8 AM to 5 PM
            hour_data = {
                'hour': f"{hour if hour <= 12 else hour-12}:00 {'AM' if hour < 12 else 'PM'}",
                'days': []
            }
            
            for day_offset in range(7):
                day_date = (start_date + timedelta(days=day_offset)).date()
                day_hour_start = datetime.combine(day_date, datetime.min.time().replace(hour=hour, minute=0))
                day_hour_end = datetime.combine(day_date, datetime.min.time().replace(hour=hour, minute=59))
                
                day_hour_appointments = appointments.filter(
                    time__range=(day_hour_start, day_hour_end)
                )
                
                hour_data['days'].append({
                    'date': day_date,
                    'appointments': day_hour_appointments
                })
            
            time_slots.append(hour_data)
        
        result['time_slots'] = time_slots
        
    elif view_type == 'month':
        # For month view, organize by day of month
        # Get the first day of the month
        first_day = start_date.replace(day=1)
        
        # Get the weekday of the first day (0 = Monday, 6 = Sunday in Python's calendar module)
        first_weekday = first_day.weekday()
        
        # Calculate days from previous month to display
        prev_month_days = []
        if first_weekday > 0:
            for i in range(first_weekday):
                prev_date = first_day - timedelta(days=first_weekday-i)
                prev_date_start = datetime.combine(prev_date.date(), datetime.min.time())
                prev_date_end = datetime.combine(prev_date.date(), datetime.max.time())
                
                prev_date_appointments = appointments.filter(
                    time__range=(prev_date_start, prev_date_end)
                )
                
                prev_month_days.append({
                    'date': prev_date.date(),
                    'day': prev_date.day,
                    'is_current_month': False,
                    'is_today': prev_date.date() == timezone.now().date(),
                    'appointments': prev_date_appointments
                })
        
        # Calculate days in current month
        current_month_days = []
        _, last_day = calendar.monthrange(first_day.year, first_day.month)
        
        for day in range(1, last_day + 1):
            current_date = first_day.replace(day=day)
            current_date_start = datetime.combine(current_date.date(), datetime.min.time())
            current_date_end = datetime.combine(current_date.date(), datetime.max.time())
            
            day_appointments = appointments.filter(
                time__range=(current_date_start, current_date_end)
            )
            
            current_month_days.append({
                'date': current_date.date(),
                'day': day,
                'is_current_month': True,
                'is_today': current_date.date() == timezone.now().date(),
                'appointments': day_appointments
            })
        
        # Calculate days from next month to display
        next_month_days = []
        total_days = len(prev_month_days) + len(current_month_days)
        if total_days < 42:  # 6 weeks of 7 days
            remaining_days = 42 - total_days
            next_month_first = first_day.replace(day=28) + timedelta(days=4)
            next_month_first = next_month_first.replace(day=1)
            
            for i in range(remaining_days):
                next_date = next_month_first + timedelta(days=i)
                next_date_start = datetime.combine(next_date.date(), datetime.min.time())
                next_date_end = datetime.combine(next_date.date(), datetime.max.time())
                
                next_date_appointments = appointments.filter(
                    time__range=(next_date_start, next_date_end)
                )
                
                next_month_days.append({
                    'date': next_date.date(),
                    'day': next_date.day,
                    'is_current_month': False,
                    'is_today': next_date.date() == timezone.now().date(),
                    'appointments': next_date_appointments
                })
        
        # Combine all days
        all_days = prev_month_days + current_month_days + next_month_days
        
        # Organize days into weeks
        weeks = []
        for i in range(0, len(all_days), 7):
            weeks.append(all_days[i:i+7])
        
        result['weeks'] = weeks
    
    return result

# @login_required
def view_appointment(request, appointment_id):
    """View for provider to see appointment details"""
    provider = get_provider(request)
    
    # Get the appointment
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=provider)
    
    # Get patient data if available
    patient = appointment.patient
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'appointment': appointment,
        'patient': patient,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/view_appointment.html", context)

# @login_required
def schedule_appointment(request):
    """View for provider to schedule a new appointment"""
    provider = get_provider(request)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, provider=provider)
        if form.is_valid():
            # Save the appointment
            appointment = form.save(commit=False)
            appointment.doctor = provider
            appointment.status = 'Scheduled'
            appointment.save()
            
            messages.success(request, "Appointment scheduled successfully!")
            return redirect('provider_appointments')
        else:
            messages.error(request, "There was an error scheduling the appointment. Please check the form.")
    else:
        form = AppointmentForm(provider=provider)
    
    # Get patients for this provider
    patients = provider.get_patients()
    
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(30):  # Next 30 days
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'patients': patients,
        'available_dates': available_dates,
        'available_times': available_times,
        'form': form,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/schedule_appointment.html", context)

# @login_required
def reschedule_appointment(request, appointment_id):
    """View for provider to reschedule an existing appointment"""
    provider = get_provider(request)
    
    # Get the appointment
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=provider)
    
    if request.method == 'POST':
        # Extract new appointment date and time
        new_date = request.POST.get('appointment_date')
        new_time = request.POST.get('appointment_time')
        
        if new_date and new_time:
            try:
                # Combine date and time
                new_datetime_str = f"{new_date} {new_time}"
                new_datetime = datetime.strptime(new_datetime_str, '%Y-%m-%d %I:%M %p')
                
                # Update the appointment
                appointment.time = new_datetime
                appointment.save()
                
                # Get reschedule reason
                reschedule_reason = request.POST.get('reschedule_reason', '')
                
                # Check if we should notify the patient
                notify_patient = request.POST.get('notify_patient') == 'on'
                
                # Handle notification logic here if needed
                
                messages.success(request, "Appointment rescheduled successfully!")
                return redirect('provider_appointments')
            except ValueError:
                messages.error(request, "Invalid date or time format. Please try again.")
        else:
            messages.error(request, "Date and time are required to reschedule an appointment.")
    
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(30):  # Next 30 days
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    # Get the patient information
    patient = appointment.patient
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'appointment': appointment,
        'patient': patient,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/reschedule_appointment.html", context)

# @login_required
def update_appointment_status(request, appointment_id):
    """View for provider to update appointment status"""
    provider = get_provider(request)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status not in ['Scheduled', 'Checked In', 'In Progress', 'Completed', 'Cancelled', 'No Show']:
            messages.error(request, "Invalid appointment status.")
            return redirect('provider_appointments')
        
        # Get the appointment
        appointment = get_object_or_404(Appointment, id=appointment_id, doctor=provider)
        
        # Check if status field exists in Appointment model
        if hasattr(appointment, 'status'):
            # Update the appointment status
            appointment.status = status
            appointment.save()
            
            messages.success(request, f"Appointment status updated to {status}.")
        else:
            # Inform the user that status field doesn't exist
            messages.error(request, "Cannot update status - status field not defined in Appointment model.")
    
    return redirect('provider_appointments')
