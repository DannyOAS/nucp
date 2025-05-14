# patient/views/email.py
from django.shortcuts import render
from patient.decorators import patient_required
from common.models import Message
from django.core.paginator import Paginator
from patient.services.message_service import MessageService

# Uncomment for API-based implementation
# import requests
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def email_view(request):
    """View for patient email dashboard"""
    patient = request.patient
    
    # Get messages from database
    inbox_messages = Message.objects.filter(
        recipient=request.user
    ).exclude(
        status='deleted'
    ).order_by('-created_at')[:5]
    
    # Count messages by status
    unread_count = Message.objects.filter(recipient=request.user, status='unread').count()
    read_count = Message.objects.filter(recipient=request.user, status='read').count()
    sent_count = Message.objects.filter(sender=request.user).count()
    archived_count = Message.objects.filter(recipient=request.user, status='archived').count()
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'inbox_messages': inbox_messages,
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'archived_count': archived_count,
        'active_section': 'email'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get message counts
    #     counts_response = requests.get(
    #         f"{api_url}messages/counts/",
    #         headers=headers
    #     )
    #     
    #     if counts_response.ok:
    #         counts = counts_response.json()
    #         unread_count = counts.get('unread', 0)
    #         read_count = counts.get('read', 0)
    #         sent_count = counts.get('sent', 0)
    #         archived_count = counts.get('archived', 0)
    #     else:
    #         unread_count = read_count = sent_count = archived_count = 0
    #     
    #     # Get recent inbox messages
    #     inbox_response = requests.get(
    #         f"{api_url}messages/inbox/?limit=5",
    #         headers=headers
    #     )
    #     
    #     if inbox_response.ok:
    #         inbox_messages = inbox_response.json()['results']
    #     else:
    #         inbox_messages = []
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'inbox_messages': inbox_messages,
    #         'unread_count': unread_count,
    #         'read_count': read_count,
    #         'sent_count': sent_count,
    #         'archived_count': archived_count,
    #         'active_section': 'email'
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading email dashboard: {str(e)}")
    
    return render(request, "patient/email.html", context)
