# patient/views/email.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

# Comment out import of nonexistent EmailService
# from patient.services.email_service import EmailService
from patient.utils import get_current_patient
from api.v1.patient.serializers import MessageSerializer
from common.models import Message

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
    
    # Generate mock data since EmailService doesn't exist
    user = patient.user
    
    # Get inbox messages (excluding deleted)
    inbox_messages = Message.objects.filter(
        recipient=user
    ).exclude(
        status='deleted'
    ).order_by('-created_at')[:5]  # Limit to 5 most recent
    
    # Count metrics
    unread_count = Message.objects.filter(
        recipient=user,
        status='unread'
    ).count()
    
    read_count = Message.objects.filter(
        recipient=user,
        status='read'
    ).count()
    
    sent_count = Message.objects.filter(
        sender=user
    ).count()
    
    archived_count = Message.objects.filter(
        recipient=user,
        status='archived'
    ).count()
    
    # Format messages using API serializer if needed
    serializer = MessageSerializer(inbox_messages, many=True)
    messages_data = serializer.data
    
    context = {
        'patient': patient_dict,
        'patient_name': patient.full_name,
        'inbox_messages': messages_data,
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'archived_count': archived_count,
        'active_section': 'email'
    }
    
    return render(request, "patient/email.html", context)

@patient_required
def compose_email(request):
    """
    View for composing and sending a new email.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Extract form data
            recipient_data = {
                'recipient_type': request.POST.get('recipient_type')
            }
            email_data = {
                'subject': request.POST.get('subject'),
                'content': request.POST.get('content')
            }
            
            # Send email via service
            result = EmailService.compose_email(
                patient_id=patient.id,
                recipient_data=recipient_data,
                email_data=email_data,
                user=request.user
            )
            
            if result.get('success', False):
                messages.success(request, "Email sent successfully!")
                return redirect('patient:patient_email')
            else:
                messages.error(request, result.get('error', "Error sending email."))
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            messages.error(request, f"Error sending email: {str(e)}")
    
    # Get recipient choices for the form
    recipient_choices = [
        ('provider', 'My Healthcare Provider'),
        ('pharmacy', 'Pharmacy'),
        ('billing', 'Billing Department')
    ]
    
    context = {
        'patient': patient_dict,
        'patient_name': patient.full_name,
        'recipient_choices': recipient_choices,
        'active_section': 'email'
    }
    
    return render(request, "patient/compose_email.html", context)

@patient_required
def view_email(request, message_id):
    """
    View a specific email with full details.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get message details from message service
        # We can reuse the MessageService for this functionality
        from patient.services.message_service import MessageService
        message_data = MessageService.get_message_details(
            message_id=message_id,
            patient_id=patient.id
        )
        
        if not message_data.get('success', False):
            messages.error(request, message_data.get('error', "Email not found."))
            return redirect('patient:patient_email')
        
        # Format message using API serializer if needed
        message_obj = message_data.get('message')
        if message_obj and hasattr(message_obj, '__dict__'):
            serializer = MessageSerializer(message_obj)
            message_data['message'] = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'message': message_data.get('message'),
            'active_section': 'email'
        }
    except Exception as e:
        logger.error(f"Error retrieving email details: {str(e)}")
        messages.error(request, "There was an error retrieving the email.")
        return redirect('patient:patient_email')
    
    return render(request, "patient/view_email.html", context)

@patient_required
def email_action(request, message_id, action):
    """
    Handle email actions like mark as read/unread, archive, delete.
    Reuses the message_action functionality.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Process email action via MessageService
        from patient.services.message_service import MessageService
        result = MessageService.perform_message_action(
            message_id=message_id,
            patient_id=patient.id,
            action=action,
            user=request.user
        )
        
        if result.get('success', False):
            # Success message based on the action
            if action == 'mark_read':
                messages.success(request, "Email marked as read.")
            elif action == 'mark_unread':
                messages.success(request, "Email marked as unread.")
            elif action == 'archive':
                messages.success(request, "Email archived.")
            elif action == 'delete':
                messages.success(request, "Email deleted.")
            else:
                messages.success(request, "Email action performed successfully.")
        else:
            messages.error(request, result.get('error', f"Error performing {action} action."))
    except Exception as e:
        logger.error(f"Error performing email action: {str(e)}")
        messages.error(request, f"Error performing action: {str(e)}")
    
    # Return to email dashboard
    return redirect('patient:patient_email')
