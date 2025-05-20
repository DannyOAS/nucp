# provider/views/dashboard.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from provider.services import ProviderService
from provider.utils import get_current_provider
from api.v1.provider.serializers import (
    AppointmentSerializer, PrescriptionSerializer,
    RecordingSessionSerializer, GeneratedDocumentSerializer
)

logger = logging.getLogger(__name__)

@login_required
def provider_dashboard(request):
    """Provider dashboard view with authenticated user."""
    # Get the current provider using our utility function
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get dashboard data from service layer
        dashboard_data = ProviderService.get_dashboard_data(provider.id)
        
        # Format appointments using API serializer if needed
        upcoming_appointments = dashboard_data.get('upcoming_appointments', [])
        if hasattr(upcoming_appointments, 'model'):
            serializer = AppointmentSerializer(upcoming_appointments, many=True)
            upcoming_appointments = serializer.data
            
        # Format prescription requests if needed
        prescription_requests = dashboard_data.get('prescription_requests', [])
        if hasattr(prescription_requests, 'model'):
            serializer = PrescriptionSerializer(prescription_requests, many=True)
            prescription_requests = serializer.data
            
        # Format AI Scribe data if needed
        ai_scribe_data = dashboard_data.get('ai_scribe_data', {})
        if 'recent_recordings' in ai_scribe_data and hasattr(ai_scribe_data['recent_recordings'], 'model'):
            serializer = RecordingSessionSerializer(ai_scribe_data['recent_recordings'], many=True)
            ai_scribe_data['recent_recordings'] = serializer.data
            
        # Format Forms/Templates data if needed
        forms_templates_data = dashboard_data.get('forms_templates_data', {})
        if 'recent_documents' in forms_templates_data and hasattr(forms_templates_data['recent_documents'], 'model'):
            serializer = GeneratedDocumentSerializer(forms_templates_data['recent_documents'], many=True)
            forms_templates_data['recent_documents'] = serializer.data
            
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': dashboard_data.get('patients', [])[:5],  # Limit to 5 for dashboard
            'appointments': upcoming_appointments,
            'prescription_requests': prescription_requests,
            'stats': dashboard_data.get('stats', {
                'today_appointments': 0,
                'completed_appointments': 0,
                'active_patients': 0,
                'pending_prescriptions': 0,
                'unread_messages': 0
            }),
            'ai_scribe_data': ai_scribe_data,
            'forms_templates_data': forms_templates_data,
            'active_section': 'dashboard',
            'today': datetime.now().date()
        }
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': [],
            'appointments': [],
            'prescription_requests': [],
            'stats': {
                'today_appointments': 0,
                'completed_appointments': 0,
                'active_patients': 0,
                'pending_prescriptions': 0,
                'unread_messages': 0
            },
            'ai_scribe_data': {
                'enabled': True,
                'recent_recordings': []
            },
            'forms_templates_data': {
                'enabled': True,
                'templates': [],
                'recent_documents': []
            },
            'active_section': 'dashboard',
            'today': datetime.now().date()
        }
    
    return render(request, "provider/dashboard.html", context)
