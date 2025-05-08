# provider/views/dashboard.py - Complete updated version

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
# from django.contrib.auth.decorators import login_required
from django.db.models import Q

from common.models import Appointment, Prescription, Message
from provider.models import Provider, RecordingSession, ClinicalNote, DocumentTemplate
from theme_name.models import PatientRegistration

def get_provider(request):
    """Helper function to get the current provider"""
    # Once login is implemented, uncomment the following:
    # return get_object_or_404(Provider, user=request.user)
    
    # For now, we'll just get the first provider or create one if needed
    provider, created = Provider.objects.get_or_create(
        id=1,
        defaults={
            'user_id': 1,  # Assuming user with ID 1 exists
            'license_number': 'TEMP123',
            'specialty': 'Family Medicine',
        }
    )
    return provider

# @login_required
def provider_dashboard(request):
    """Provider dashboard view with direct ORM access"""
    provider = get_provider(request)
    
    # Get today's date for filtering
    today = timezone.now().date()
    end_of_day = datetime.combine(today, datetime.max.time())
    start_of_day = datetime.combine(today, datetime.min.time())
    
    # Get appointments using ORM
    upcoming_appointments = Appointment.objects.filter(
        doctor=provider, 
        time__gte=timezone.now()
    ).order_by('time')[:3]
    
    today_appointments = Appointment.objects.filter(
        doctor=provider,
        time__range=(start_of_day, end_of_day)
    ).count()
    
    # Check if status field exists in Appointment model
    # If not, skip status filtering
    use_status_field = hasattr(Appointment, 'status')
    
    if use_status_field:
        completed_appointments = Appointment.objects.filter(
            doctor=provider, 
            status='Completed'
        ).count()
    else:
        # Alternative: just count all past appointments
        completed_appointments = Appointment.objects.filter(
            doctor=provider,
            time__lt=timezone.now()
        ).count()
    
    # Get patients - check if provider field exists in PatientRegistration
    if hasattr(PatientRegistration, 'provider'):
        # Use the provider field if it exists
        patients = PatientRegistration.objects.filter(provider=provider)
        active_patients = patients.count()
    else:
        # Alternative approach: Get patients from appointments
        patient_ids = Appointment.objects.filter(doctor=provider).values_list('patient_id', flat=True).distinct()
        patients = PatientRegistration.objects.filter(id__in=patient_ids)
        active_patients = patients.count()
    
    # Get unread messages - check if read or read_at field exists
    if hasattr(Message, 'read'):
        unread_messages = Message.objects.filter(
            recipient=provider.user,
            read=False
        ).count()
    elif hasattr(Message, 'read_at'):
        # If using read_at, messages are unread if read_at is None/null
        unread_messages = Message.objects.filter(
            recipient=provider.user,
            read_at__isnull=True
        ).count()
    else:
        # Fallback if neither field exists - use status field if available
        if hasattr(Message, 'status'):
            unread_messages = Message.objects.filter(
                recipient=provider.user,
                status='unread'
            ).count()
        else:
            # Last resort - just count all messages
            unread_messages = Message.objects.filter(
                recipient=provider.user
            ).count()
    
    # Get pending prescription requests
    prescription_requests = Prescription.objects.filter(
        doctor=provider,
        status='Pending'
    )
    
    # Get AI Scribe data
    ai_scribe_data = {
        'enabled': True,
        'recent_recordings': RecordingSession.objects.filter(
            provider=provider
        ).order_by('-start_time')[:2]  # Get 2 most recent recordings
    }
    
    # Get Templates data
    forms_templates_data = {
        'enabled': True,
        'templates': DocumentTemplate.objects.filter(is_active=True)[:5],
        'recent_documents': provider.generated_documents.all().order_by('-created_at')[:3]
    }
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'patients': patients[:5],  # Limit to 5 for dashboard
        'appointments': upcoming_appointments,
        'prescription_requests': prescription_requests,
        'stats': {
            'today_appointments': today_appointments,
            'completed_appointments': completed_appointments,
            'active_patients': active_patients,
            'pending_prescriptions': prescription_requests.count(),
            'unread_messages': unread_messages
        },
        'ai_scribe_data': ai_scribe_data,
        'forms_templates_data': forms_templates_data,
        'active_section': 'dashboard',
        'today': datetime.now().date()
    }
    
    return render(request, "provider/dashboard.html", context)
