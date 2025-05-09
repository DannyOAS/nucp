"""Dashboard view for provider portal."""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta

from common.models import Appointment, Prescription, Message
from provider.models import Provider, RecordingSession, DocumentTemplate
from provider.utils import get_current_provider
import logging

logger = logging.getLogger(__name__)

@login_required
def provider_dashboard(request):
    """Provider dashboard view with authenticated user."""
    # Get the current provider using our utility function
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get today's date for filtering
    today = timezone.now().date()
    end_of_day = datetime.combine(today, datetime.max.time())
    start_of_day = datetime.combine(today, datetime.min.time())
    
    # Get appointments using ORM - filtered for this provider
    try:
        upcoming_appointments = Appointment.objects.filter(
            doctor=provider, 
            time__gte=timezone.now()
        ).order_by('time')[:3]
        
        today_appointments = Appointment.objects.filter(
            doctor=provider,
            time__range=(start_of_day, end_of_day)
        ).count()
        
        # Check if status field exists in Appointment model
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
    except Exception as e:
        logger.error(f"Error retrieving appointments: {str(e)}")
        upcoming_appointments = []
        today_appointments = 0
        completed_appointments = 0
    
    # Get patients for this provider
    try:
        # Method 1: Get patients directly assigned to provider if field exists
        from theme_name.models import PatientRegistration
        
        if hasattr(PatientRegistration, 'provider'):
            # Get patients directly assigned to this provider
            patients = PatientRegistration.objects.filter(provider=provider)
            active_patients = patients.count()
        else:
            # Method 2: Get patient IDs from appointments with this provider
            patient_ids = Appointment.objects.filter(
                doctor=provider
            ).values_list('patient_id', flat=True).distinct()
            
            # Get the patient objects
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
            active_patients = patients.count()
    except Exception as e:
        logger.error(f"Error retrieving patients: {str(e)}")
        patients = []
        active_patients = 0
    
    # Get message count
    try:
        # Use authenticated user for messages
        unread_messages = Message.objects.filter(
            recipient=request.user,
            read=False
        ).count()
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        unread_messages = 0
    
    # Get pending prescription requests
    try:
        prescription_requests = Prescription.objects.filter(
            doctor=provider,
            status='Pending'
        )
    except Exception as e:
        logger.error(f"Error retrieving prescriptions: {str(e)}")
        prescription_requests = []
    
    # Get AI Scribe data
    try:
        ai_scribe_data = {
            'enabled': True,
            'recent_recordings': RecordingSession.objects.filter(
                provider=provider
            ).order_by('-start_time')[:2]  # Get 2 most recent recordings
        }
    except Exception as e:
        logger.error(f"Error retrieving AI Scribe data: {str(e)}")
        ai_scribe_data = {
            'enabled': True,
            'recent_recordings': []
        }
    
    # Get Templates data
    try:
        forms_templates_data = {
            'enabled': True,
            'templates': DocumentTemplate.objects.filter(is_active=True)[:5],
            'recent_documents': provider.generated_documents.all().order_by('-created_at')[:3]
        }
    except Exception as e:
        logger.error(f"Error retrieving form templates: {str(e)}")
        forms_templates_data = {
            'enabled': True,
            'templates': [],
            'recent_documents': []
        }
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {request.user.last_name}",
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
