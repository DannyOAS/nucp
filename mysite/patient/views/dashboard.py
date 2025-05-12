# patient/views/dashboard.py
from django.shortcuts import render
from patient.decorators import patient_required
from common.models import Message, Appointment, Prescription

@patient_required
def patient_dashboard(request):
    """Patient dashboard view using database models"""
    patient = request.patient  # Injected by decorator
    
    # Get recent appointments - use request.user since Appointment.patient is a User FK
    appointments = Appointment.objects.filter(patient=request.user).order_by('-time')[:5]
    
    # Get recent prescriptions - use request.user since Prescription.patient is a User FK
    prescriptions = Prescription.objects.filter(patient=request.user).order_by('-created_at')[:5]
    
    # Get recent messages
    recent_messages = Message.objects.filter(
        recipient=request.user
    ).exclude(
        status='deleted'
    ).order_by('-created_at')[:5]
    
    # Get unread message count
    unread_messages_count = Message.objects.filter(
        recipient=request.user, 
        status='unread'
    ).count()
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'appointments': appointments,
        'prescriptions': prescriptions,
        'recent_messages': recent_messages,
        'unread_messages_count': unread_messages_count,
        'active_section': 'dashboard',
    }
    
    return render(request, "patient/dashboard.html", context)

def get_base_context(active_section):
    """Helper function to get base context for patient views"""
    return {
        'active_section': active_section
    }
