# views/provider_views/appointments.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta, date
import calendar
import logging

from theme_name.repositories import ProviderRepository
from provider.utils import get_current_provider
# Import the renamed AppointmentService
from provider.services.appointment_service import AppointmentService

logger = logging.getLogger(__name__)

@login_required
def provider_appointments(request):
    """Provider appointments view with calendar integration"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Handle view type selection
    view_type = request.GET.get('view', 'week')  # Default to week view
    
    # Handle date navigation
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Determine date range based on view type
    if view_type == 'day':
        start_date = datetime.combine(selected_date, datetime.min.time())
        end_date = datetime.combine(selected_date, datetime.max.time())
        date_display = selected_date.strftime('%B %d, %Y')
        
        # For day view navigation
        prev_date = (selected_date - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (selected_date + timedelta(days=1)).strftime('%Y-%m-%d')
        
    elif view_type == 'week':
        # Start from Monday of the week containing selected_date
        start_date = datetime.combine(
            selected_date - timedelta(days=selected_date.weekday()),
            datetime.min.time()
        )
        end_date = start_date + timedelta(days=7)
        
        # Date range display
        date_display = f"{start_date.strftime('%b %d')} - {(end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
        
        # For week view navigation
        prev_date = (selected_date - timedelta(days=7)).strftime('%Y-%m-%d')
        next_date = (selected_date + timedelta(days=7)).strftime('%Y-%m-%d')
        
    elif view_type == 'month':
        # Start from the 1st of the month
        start_date = datetime.combine(
            date(selected_date.year, selected_date.month, 1),
            datetime.min.time()
        )
        
        # End on the last day of the month
        _, last_day = calendar.monthrange(selected_date.year, selected_date.month)
        end_date = datetime.combine(
            date(selected_date.year, selected_date.month, last_day),
            datetime.max.time()
        )
        
        date_display = selected_date.strftime('%B %Y')
        
        # For month view navigation
        if selected_date.month == 1:
            prev_date = date(selected_date.year - 1, 12, 1).strftime('%Y-%m-%d')
        else:
            prev_date = date(selected_date.year, selected_date.month - 1, 1).strftime('%Y-%m-%d')
            
        if selected_date.month == 12:
            next_date = date(selected_date.year + 1, 1, 1).strftime('%Y-%m-%d')
        else:
            next_date = date(selected_date.year, selected_date.month + 1, 1).strftime('%Y-%m-%d')
    else:
        # Default to week view if invalid view type
        view_type = 'week'
        start_date = datetime.combine(
            selected_date - timedelta(days=selected_date.weekday()),
            datetime.min.time()
        )
        end_date = start_date + timedelta(days=7)
        date_display = f"{start_date.strftime('%b %d')} - {(end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
        prev_date = (selected_date - timedelta(days=7)).strftime('%Y-%m-%d')
        next_date = (selected_date + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Get appointments using enhanced service with calendar integration
    try:
        appointments = AppointmentService.get_provider_appointments(
            provider_id=provider.id,
            start_date=start_date,
            end_date=end_date,
            view_type=view_type
        )
        
        # Process appointments for calendar display
        calendar_data = process_appointments_for_calendar(appointments, start_date, end_date, view_type)
        
        # Get today's appointments for the list view
        today = timezone.now().date()
        todays_appointments = [
            appt for appt in appointments 
            if get_appointment_date(appt) == today
        ]
        
        # Calculate appointment statistics
        today_count = len(todays_appointments)
        upcoming_count = len([a for a in appointments if a.get('status') == 'Scheduled'])
        completed_count = len([a for a in appointments if a.get('status') == 'Completed'])
        cancelled_count = len([a for a in appointments if a.get('status') == 'Cancelled'])
    except Exception as e:
        logger.error(f"Error retrieving appointments: {str(e)}")
        appointments = []
        calendar_data = {}
        todays_appointments = []
        today_count = 0
        upcoming_count = 0
        completed_count = 0
        cancelled_count = 0
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
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
    """Extract date from appointment time string."""
    try:
        if appointment.get('time'):
            time_str = appointment.get('time')
            if '-' in time_str:
                date_part = time_str.split('-')[0].strip()
                for fmt in ['%b %d, %Y', '%B %d, %Y']:
                    try:
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
            hour_appointments = []
            for appointment in appointments:
                # Extract date and time from appointment time
                appointment_date = get_appointment_date(appointment)
                if appointment_date and appointment_date == start_date.date():
                    # Extract hour from appointment time
                    time_parts = appointment.get('time', '').split('-')
                    if len(time_parts) >= 2:
                        time_str = time_parts[1].strip()
                        try:
                            # Try different time formats
                            for fmt in ['%I:%M %p', '%H:%M', '%I:%M%p']:
                                try:
                                    appt_time = datetime.strptime(time_str, fmt)
                                    if appt_time.hour == hour:
                                        hour_appointments.append(appointment)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            pass
            
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
            day_appointments = []
            
            for appointment in appointments:
                # Extract date from appointment time
                appointment_date = get_appointment_date(appointment)
                if appointment_date and appointment_date == day_date:
                    day_appointments.append(appointment)
            
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
                day_hour_appointments = []
                
                for appointment in appointments:
                    # Extract date from appointment time
                    appointment_date = get_appointment_date(appointment)
                    if appointment_date and appointment_date == day_date:
                        # Extract hour from appointment time
                        time_parts = appointment.get('time', '').split('-')
                        if len(time_parts) >= 2:
                            time_str = time_parts[1].strip()
                            try:
                                # Try different time formats
                                for fmt in ['%I:%M %p', '%H:%M', '%I:%M%p']:
                                    try:
                                        appt_time = datetime.strptime(time_str, fmt)
                                        if appt_time.hour == hour:
                                            day_hour_appointments.append(appointment)
                                        break
                                    except ValueError:
                                        continue
                            except Exception:
                                pass
                
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
                prev_date_appointments = []
                
                for appointment in appointments:
                    appointment_date = get_appointment_date(appointment)
                    if appointment_date and appointment_date == prev_date.date():
                        prev_date_appointments.append(appointment)
                
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
            day_appointments = []
            
            for appointment in appointments:
                appointment_date = get_appointment_date(appointment)
                if appointment_date and appointment_date == current_date.date():
                    day_appointments.append(appointment)
            
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
                next_date_appointments = []
                
                for appointment in appointments:
                    appointment_date = get_appointment_date(appointment)
                    if appointment_date and appointment_date == next_date.date():
                        next_date_appointments.append(appointment)
                
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


@login_required
def view_appointment(request, appointment_id):
    """View for provider to see appointment details"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get the appointment
    try:
        provider_appointments = AppointmentService.get_provider_appointments(provider.id)
        
        appointment = None
        for appt in provider_appointments:
            if appt.get('id') == appointment_id:
                appointment = appt
                break
        
        if not appointment:
            messages.error(request, "Appointment not found.")
            return redirect('provider_appointments')
        
        # Get patient data if available
        patient = None
        from theme_name.repositories import PatientRepository
        if appointment.get('patient_id'):
            patient = PatientRepository.get_by_id(appointment.get('patient_id'))
    except Exception as e:
        logger.error(f"Error retrieving appointment details: {str(e)}")
        messages.error(request, "There was an error retrieving the appointment details.")
        return redirect('provider_appointments')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'appointment': appointment,
        'patient': patient,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/view_appointment.html", context)

@login_required
def schedule_appointment(request):
    """View for provider to schedule a new appointment"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        # Extract appointment data from the form
        try:
            appointment_data = {
                'doctor': f"Dr. {provider_dict['last_name']}",
                'time': request.POST.get('appointment_date') + ' - ' + request.POST.get('appointment_time'),
                'type': request.POST.get('appointment_type'),
                'reason': request.POST.get('reason'),
                'location': request.POST.get('location', 'Northern Health Clinic'),
                'notes': request.POST.get('notes', ''),
                'patient_id': request.POST.get('patient_id'),
                'patient_name': request.POST.get('patient_name'),
                'status': 'Scheduled'
            }
            
            # Schedule the appointment
            appointment = AppointmentService.schedule_appointment(
                appointment_data=appointment_data,
                patient_id=request.POST.get('patient_id'),
                provider_id=provider.id  # Use authenticated provider
            )
            
            if appointment:
                messages.success(request, "Appointment scheduled successfully!")
                return redirect('provider_appointments')
            else:
                messages.error(request, "There was an error scheduling the appointment. Please try again.")
        except Exception as e:
            logger.error(f"Error scheduling appointment: {str(e)}")
            messages.error(request, f"There was an error scheduling the appointment: {str(e)}")
    
    # For GET requests, display the scheduling form
    # Get patients for this provider
    try:
        # Get patients for this provider
        from theme_name.models import PatientRegistration
        
        if hasattr(PatientRegistration, 'provider'):
            # Direct provider relationship
            patients = PatientRegistration.objects.filter(provider=provider)
        else:
            # Get from appointments
            from common.models import Appointment
            patient_ids = Appointment.objects.filter(
                doctor=provider
            ).values_list('patient_id', flat=True).distinct()
            
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
    except Exception as e:
        logger.error(f"Error retrieving patients for provider: {str(e)}")
        # Fallback to repository during transition
        from theme_name.repositories import ProviderRepository
        patients = ProviderRepository.get_patients(provider.id)
    
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(30):  # Next 30 days
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'patients': patients,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/schedule_appointment.html", context)

@login_required
def reschedule_appointment(request, appointment_id):
    """View for provider to reschedule an existing appointment"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get the appointment
    try:
        provider_appointments = AppointmentService.get_provider_appointments(provider.id)
        
        appointment = None
        for appt in provider_appointments:
            if appt.get('id') == appointment_id:
                appointment = appt
                break
        
        if not appointment:
            messages.error(request, "Appointment not found.")
            return redirect('provider_appointments')
    except Exception as e:
        logger.error(f"Error retrieving appointment: {str(e)}")
        messages.error(request, "There was an error retrieving the appointment.")
        return redirect('provider_appointments')
    
    if request.method == 'POST':
        try:
            # Extract new appointment time from form
            new_time_data = {
                'time': request.POST.get('appointment_date') + ' - ' + request.POST.get('appointment_time')
            }
            
            # Get patient ID from the appointment
            patient_id = appointment.get('patient_id')
            
            # Get reschedule reason
            reschedule_reason = request.POST.get('reschedule_reason', '')
            
            # Check if we should notify the patient
            notify_patient = request.POST.get('notify_patient') == 'on'
            
            # Reschedule the appointment
            result = AppointmentService.reschedule_appointment(
                appointment_id=appointment_id,
                new_time_data=new_time_data,
                patient_id=patient_id,
                provider_initiated=True,
                reschedule_reason=reschedule_reason,
                notify_patient=notify_patient
            )
            
            if result.get('success', False):
                messages.success(request, "Appointment rescheduled successfully!")
                return redirect('provider_appointments')
            else:
                messages.error(request, f"There was an error rescheduling the appointment: {result.get('error', 'Please try again.')}")
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            messages.error(request, f"There was an error rescheduling the appointment: {str(e)}")
    
    # For GET requests, display the rescheduling form
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(30):  # Next 30 days
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    # Get the patient information
    patient = None
    if appointment.get('patient_id'):
        from theme_name.repositories import PatientRepository
        patient = PatientRepository.get_by_id(appointment.get('patient_id'))
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'appointment': appointment,
        'patient': patient,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/reschedule_appointment.html", context)

@login_required
def update_appointment_status(request, appointment_id):
    """View for provider to update appointment status"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status not in ['Scheduled', 'Checked In', 'In Progress', 'Completed', 'Cancelled', 'No Show']:
            messages.error(request, "Invalid appointment status.")
            return redirect('provider_appointments')
        
        try:
            # Get the appointment
            provider_appointments = AppointmentService.get_provider_appointments(provider.id)
            appointment = None
            
            for appt in provider_appointments:
                if appt.get('id') == appointment_id:
                    appointment = appt
                    break
            
            if not appointment:
                messages.error(request, "Appointment not found.")
                return redirect('provider_appointments')
            
            # Update the appointment status
            from theme_name.repositories import AppointmentRepository
            updated_appointment = AppointmentRepository.update(
                appointment_id,
                {'status': status}
            )
            
            if updated_appointment:
                messages.success(request, f"Appointment status updated to {status}.")
                
                # If cancelling, also handle calendar removal
                if status == 'Cancelled':
                    result = AppointmentService.cancel_appointment(
                        appointment_id=appointment_id,
                        provider_initiated=True
                    )
                    if not result.get('success', False):
                        messages.warning(request, "Appointment status was updated, but there was an issue syncing with the calendar.")
            else:
                messages.error(request, "There was an error updating the appointment status.")
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            messages.error(request, f"There was an error updating the appointment status: {str(e)}")
    
    return redirect('provider_appointments')
