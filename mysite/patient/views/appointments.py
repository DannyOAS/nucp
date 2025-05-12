# patient/views/appointments.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from patient.decorators import patient_required
from common.models import Appointment
from provider.models import Provider

@patient_required
def appointments_view(request):
    """Patient appointments view using database models"""
    patient = request.patient
    
    # Get appointments - use request.user instead of patient
    today = timezone.now()
    upcoming_appointments = Appointment.objects.filter(
        patient=request.user,  # Use request.user, not patient
        time__gte=today
    ).order_by('time')
    
    past_appointments = Appointment.objects.filter(
        patient=request.user,  # Use request.user, not patient
        time__lt=today
    ).order_by('-time')[:10]  # Last 10 past appointments
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'today': today,
        'active_section': 'appointments'
    }
    
    return render(request, "patient/appointments.html", context)
@patient_required
def schedule_appointment(request):
    """Schedule new appointment using database models"""
    patient = request.patient
    
    if request.method == 'POST':
        # Get form data
        provider_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        appointment_type = request.POST.get('appointment_type')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '')
        
        try:
            # Parse datetime
            datetime_str = f"{appointment_date} {appointment_time}"
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')
            appointment_datetime = timezone.make_aware(appointment_datetime)
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor_id=provider_id,
                time=appointment_datetime,
                type=appointment_type,
                reason=reason,
                notes=notes,
                status='Scheduled'
            )
            
            messages.success(request, "Appointment scheduled successfully!")
            return redirect('patient:patient_appointments')
            
        except Exception as e:
            messages.error(request, f"Error scheduling appointment: {str(e)}")
    
    # For GET requests, display the scheduling form
    available_providers = Provider.objects.filter(is_active=True)
    
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(14):  # Next two weeks
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'available_providers': available_providers,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "patient/schedule_appointment.html", context)

@login_required
def reschedule_appointment(request, appointment_id):
    """View for patient to reschedule an existing appointment"""
    patient = PatientRepository.get_current(request)
    appointment = AppointmentRepository.get_by_id(appointment_id)
    
    if not appointment:
        messages.error(request, "Appointment not found.")
        return redirect('patient_appointments')
    
    if request.method == 'POST':
        # Extract new appointment time from form
        new_time_data = {
            'time': request.POST.get('appointment_date') + ' - ' + request.POST.get('appointment_time')
        }
        
        # Reschedule the appointment
        result = AppointmentService.reschedule_appointment(
            appointment_id=appointment_id,
            new_time_data=new_time_data,
            patient_id=patient['id']
        )
        
        if result['success']:
            messages.success(request, "Appointment rescheduled successfully!")
            return redirect('patient_appointments')
        else:
            messages.error(request, f"There was an error rescheduling your appointment: {result.get('error', 'Please try again.')}")
    
    # For GET requests, display the rescheduling form
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(14):  # Next two weeks
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'appointment': appointment,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "patient/reschedule_appointment.html", context)

@login_required
def cancel_appointment(request, appointment_id):
    """View for patient to cancel an appointment"""
    patient = PatientRepository.get_current(request)
    
    if request.method == 'POST':
        # Cancel the appointment
        result = AppointmentService.cancel_appointment(
            appointment_id=appointment_id,
            patient_id=patient['id']
        )
        
        if result['success']:
            messages.success(request, "Appointment cancelled successfully.")
        else:
            messages.error(request, f"There was an error cancelling your appointment: {result.get('error', 'Please try again.')}")
    
    return redirect('patient_appointments')
