# views/provider_views/appointments.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from ...repositories import ProviderRepository
# Import the renamed AppointmentService
from ...services.appointment_service import AppointmentService

def provider_appointments(request):
    """Provider appointments view"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get appointments
    appointments = AppointmentService.get_provider_appointments(provider_id)
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'appointments': appointments,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/appointments.html", context)

def schedule_appointment(request):
    """View for provider to schedule a new appointment"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    if request.method == 'POST':
        # Extract appointment data from the form
        appointment_data = {
            'doctor': f"Dr. {provider['last_name']}",
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
            provider_id=provider_id
        )
        
        if appointment:
            messages.success(request, "Appointment scheduled successfully!")
            return redirect('provider_appointments')
        else:
            messages.error(request, "There was an error scheduling the appointment. Please try again.")
    
    # For GET requests, display the scheduling form
    # Get patients for this provider
    patients = ProviderRepository.get_patients(provider_id)
    
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(30):  # Next 30 days
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'patients': patients,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/schedule_appointment.html", context)

def view_appointment(request, appointment_id):
    """View for provider to see appointment details"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get the appointment
    appointment = None
    provider_appointments = AppointmentService.get_provider_appointments(provider_id)
    
    for appt in provider_appointments:
        if appt.get('id') == appointment_id:
            appointment = appt
            break
    
    if not appointment:
        messages.error(request, "Appointment not found.")
        return redirect('provider_appointments')
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'appointment': appointment,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/view_appointment.html", context)

def update_appointment_status(request, appointment_id):
    """View for provider to update appointment status"""
    provider_id = 1  # In production, get from request.user
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status not in ['Scheduled', 'Checked In', 'In Progress', 'Completed', 'Cancelled', 'No Show']:
            messages.error(request, "Invalid appointment status.")
            return redirect('provider_appointments')
        
        # Get the appointment
        provider_appointments = AppointmentService.get_provider_appointments(provider_id)
        appointment = None
        
        for appt in provider_appointments:
            if appt.get('id') == appointment_id:
                appointment = appt
                break
        
        if not appointment:
            messages.error(request, "Appointment not found.")
            return redirect('provider_appointments')
        
        # Update the appointment status
        updated_appointment = AppointmentRepository.update(
            appointment_id,
            {'status': status}
        )
        
        if updated_appointment:
            messages.success(request, f"Appointment status updated to {status}.")
        else:
            messages.error(request, "There was an error updating the appointment status.")
    
    return redirect('provider_appointments')

def reschedule_appointment(request, appointment_id):
    """View for provider to reschedule an existing appointment"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get the appointment
    appointment = None
    provider_appointments = AppointmentService.get_provider_appointments(provider_id)
    
    for appt in provider_appointments:
        if appt.get('id') == appointment_id:
            appointment = appt
            break
    
    if not appointment:
        messages.error(request, "Appointment not found.")
        return redirect('provider_appointments')
    
    if request.method == 'POST':
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
        
        if result['success']:
            messages.success(request, "Appointment rescheduled successfully!")
            return redirect('provider_appointments')
        else:
            messages.error(request, f"There was an error rescheduling the appointment: {result.get('error', 'Please try again.')}")
    
    # For GET requests, display the rescheduling form
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(30):  # Next 30 days
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'appointment': appointment,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/reschedule_appointment.html", context)
