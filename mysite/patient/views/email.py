# patient/views/email.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

#from patient.services.email_service import EmailService
from patient.utils import get_current_patient
from api.v1.patient.serializers import MessageSerializer

logger = logging.getLogger(__name__)

@patient_required
def email_view(request):
    """
    Patient email dashboard view showing inbox and message counts.
    Uses service layer for data retrieval and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get email dashboard data from service
        email_data = EmailService.get_email_dashboard(patient.id)
        
        # Format messages using API serializer if needed
        inbox_messages = email_data.get('inbox_messages', [])
        if hasattr(inbox_messages, 'model'):
            serializer = MessageSerializer(inbox_messages, many=True)
            email_data['inbox_messages'] = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'inbox_messages': email_data.get('inbox_messages', []),
            'unread_count': email_data.get('unread_count', 0),
            'read_count': email_data.get('read_count', 0),
            'sent_count': email_data.get('sent_count', 0),
            'archived_count': email_data.get('archived_count', 0),
            'active_section': 'email'
        }
    except Exception as e:
        logger.error(f"Error retrieving email dashboard: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'inbox_messages': [],
            'unread_count': 0,
            'read_count': 0,
            'sent_count': 0,
            'archived_count': 0,
            'active_section': 'email'
        }
        messages.error(request, "There was an error loading your email dashboard.")
    
    return render(request, "patient/email.html", context)
