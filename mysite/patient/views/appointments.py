# views/patient_views/appointments.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from theme_name.repositories import PatientRepository, AppointmentRepository
# Import the renamed AppointmentService
from common.services.appointment_service import AppointmentService

def appointments_view(request):
    """Patient appointments view with calendar integration"""
    patient = PatientRepository.get_current(request)
    
    # Get appointments using service with calendar integration
    appointment_data = AppointmentService.get_appointments_dashboard(patient['id'])
    
    # Add the current date for template usage
    today = timezone.now()
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'today': today,
        'appointments': appointment_data['upcoming_appointments'],
        'past_appointments': appointment_data['past_appointments'],
        'active_section': 'appointments'
    }
    
    return render(request, "patient/appointments.html", context)

def schedule_appointment(request):
    """View for patient to schedule a new appointment"""
    patient = PatientRepository.get_current(request)
    
    if request.method == 'POST':
        # Extract appointment data from the form
        appointment_data = {
            'doctor': request.POST.get('doctor'),
            'time': request.POST.get('appointment_date') + ' - ' + request.POST.get('appointment_time'),
            'type': request.POST.get('appointment_type'),
            'reason': request.POST.get('reason'),
            'location': request.POST.get('location', 'Northern Health Clinic'),
            'notes': request.POST.get('notes', ''),
            'patient_id': patient['id'],
            'patient_name': f"{patient['first_name']} {patient['last_name']}",
            'status': 'Scheduled'
        }
        
        # Determine provider ID from doctor name
        doctor_name = request.POST.get('doctor', '')
        provider_id = None
        
        # In a real implementation, you would look up the provider by name
        # For this example, we'll extract from format "Dr. Smith"
        if doctor_name.startswith('Dr. '):
            last_name = doctor_name[4:]
            # Find provider by last name - simplified example
            if last_name == 'Johnson':
                provider_id = 1
            elif last_name == 'Smith':
                provider_id = 2
            elif last_name == 'Wilson':
                provider_id = 3
        
        # Schedule the appointment
        appointment = AppointmentService.schedule_appointment(
            appointment_data=appointment_data,
            patient_id=patient['id'],
            provider_id=provider_id
        )
        
        if appointment:
            messages.success(request, "Appointment scheduled successfully!")
            return redirect('patient_appointments')
        else:
            messages.error(request, "There was an error scheduling your appointment. Please try again.")
    
    # For GET requests, display the scheduling form
    # Get available providers for dropdown
    # In a real implementation, this would come from your provider repository
    available_providers = [
        {'id': 1, 'name': 'Johnson', 'speciality': 'Family Medicine'},
        {'id': 2, 'name': 'Smith', 'speciality': 'Internal Medicine'},
        {'id': 3, 'name': 'Wilson', 'speciality': 'Cardiology'}
    ]
    
    # Generate available time slots
    # In a real implementation, this would check the provider's calendar for availability
    available_dates = []
    start_date = timezone.now().date()
    for i in range(14):  # Next two weeks
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'available_providers': available_providers,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "patient/schedule_appointment.html", context)

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
