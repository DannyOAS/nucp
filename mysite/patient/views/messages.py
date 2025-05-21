# patient/views/messages.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
from patient.decorators import patient_required
import logging

from patient.services.message_service import MessageService
from patient.utils import get_current_patient
from api.v1.patient.serializers import MessageSerializer

logger = logging.getLogger(__name__)

@patient_required
def patient_messages(request):
    """
    Patient inbox view showing received messages.
    Uses service layer for data retrieval and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get messages data from service
        messages_data = MessageService.get_patient_messages(patient.id)
        
        # Format messages using API serializer if needed
        messages_list = messages_data.get('messages', [])
        if hasattr(messages_list, 'model'):
            serializer = MessageSerializer(messages_list, many=True)
            messages_data['messages'] = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'messages': messages_data.get('messages', []),
            'unread_count': messages_data.get('unread_count', 0),
            'active_section': 'messages'
        }
    except Exception as e:
        logger.error(f"Error retrieving messages: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'messages': [],
            'unread_count': 0,
            'active_section': 'messages'
        }
        django_messages.error(request, "There was an error loading your messages.")
    
    return render(request, "patient/messages.html", context)

@patient_required
def patient_compose_message(request):
    """
    Compose a new message to a provider.
    Uses service layer for recipient info and message sending.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process message creation via service
            message_data = {
                'subject': request.POST.get('subject'),
                'content': request.POST.get('message'),
                'recipient_type': request.POST.get('recipient_type')
            }
            
            result = MessageService.send_patient_message(
                patient_id=patient.id,
                message_data=message_data,
                user=request.user
            )
            
            if result.get('success', False):
                django_messages.success(request, "Message sent successfully!")
                return redirect('patient:patient_messages')
            else:
                django_messages.error(request, result.get('error', "Error sending message."))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            django_messages.error(request, f"Error sending message: {str(e)}")
    
    # For GET requests, prepare the compose form with available recipients
    try:
        # Get compose form data from service
        compose_data = MessageService.get_compose_form_data(patient.id)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'recipient_choices': compose_data.get('recipient_choices', []),
            'active_section': 'messages'
        }
    except Exception as e:
        logger.error(f"Error preparing compose form: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'recipient_choices': [],
            'active_section': 'messages'
        }
        django_messages.error(request, "There was an error preparing the message form.")
    
    return render(request, "patient/compose_message.html", context)

@patient_required
def patient_view_message(request, message_id):
    """
    View a specific message with full details.
    Uses service layer for data retrieval and verification.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get message details from service
        message_data = MessageService.get_message_details(
            message_id=message_id,
            patient_id=patient.id
        )
        
        if not message_data.get('success', False):
            django_messages.error(request, message_data.get('error', "Message not found."))
            return redirect('patient:patient_messages')
        
        # Format message using API serializer if needed
        message_obj = message_data.get('message')
        if message_obj and hasattr(message_obj, '__dict__'):
            serializer = MessageSerializer(message_obj)
            message_data['message'] = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'message': message_data.get('message'),
            'active_section': 'messages'
        }
    except Exception as e:
        logger.error(f"Error retrieving message details: {str(e)}")
        django_messages.error(request, "There was an error retrieving the message.")
        return redirect('patient:patient_messages')
    
    return render(request, "patient/view_message.html", context)

@patient_required
def patient_message_action(request, message_id, action):
    """
    Handle message actions like mark as read/unread, archive, delete.
    Uses service layer for action processing.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Process message action via service
        result = MessageService.perform_message_action(
            message_id=message_id,
            patient_id=patient.id,
            action=action,
            user=request.user
        )
        
        if result.get('success', False):
            # Success message based on the action
            if action == 'mark_read':
                django_messages.success(request, "Message marked as read.")
            elif action == 'mark_unread':
                django_messages.success(request, "Message marked as unread.")
            elif action == 'archive':
                django_messages.success(request, "Message archived.")
            elif action == 'delete':
                django_messages.success(request, "Message deleted.")
            else:
                django_messages.success(request, "Message action performed successfully.")
        else:
            django_messages.error(request, result.get('error', f"Error performing {action} action."))
    except Exception as e:
        logger.error(f"Error performing message action: {str(e)}")
        django_messages.error(request, f"Error performing action: {str(e)}")
    
    # Determine the appropriate redirect based on the referring page
    referer = request.META.get('HTTP_REFERER', '')
    if '/view_message/' in referer:
        # If we were viewing the message, go back to inbox
        return redirect('patient:patient_messages')
    else:
        # Otherwise, stay on the current page
        return redirect('patient:patient_messages')
