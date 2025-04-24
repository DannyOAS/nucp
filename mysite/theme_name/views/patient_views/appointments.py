from django.shortcuts import render, redirect
from ...repositories import PatientRepository, AppointmentRepository
from ...services import AppointmentService

def appointments_view(request):
    """Patient appointments view"""
    patient = PatientRepository.get_current(request)
    
    # Get appointments
    appointments = AppointmentRepository.get_upcoming_for_patient(patient['id'])
    past_appointments = AppointmentRepository.get_past_for_patient(patient['id'])
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'appointments': appointments,
        'past_appointments': past_appointments,
        'active_section': 'appointments'
    }
    
    return render(request, "patient/appointments.html", context)
