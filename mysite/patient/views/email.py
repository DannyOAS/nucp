# patient/views/email.py - Updated to use AppointmentService for providers

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.email_service import EmailService
from patient.services.appointment_service import AppointmentService  # ADD THIS IMPORT
from patient.utils import get_current_patient
from api.v1.patient.serializers import MessageSerializer
from common.models import Message

logger = logging.getLogger(__name__)

@patient_required
def email_view(request):
    """
    Patient email dashboard view showing inbox and message counts.
    Uses EmailService for data retrieval and AppointmentService for provider data.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get email dashboard data from EmailService
        email_data = EmailService.get_email_dashboard(patient.id)
        
        # Get healthcare providers from AppointmentService - UPDATED
        provider_data = AppointmentService.get_patient_healthcare_providers(patient.id)
        
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
            'providers': provider_data.get('healthcare_providers', []),  # FROM SERVICE
            'active_section': 'email'
        }
    except Exception as e:
        logger.error(f"Error retrieving email dashboard data: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'inbox_messages': [],
            'unread_count': 0,
            'read_count': 0,
            'sent_count': 0,
            'archived_count': 0,
            'providers': [],  # Empty fallback
            'active_section': 'email'
        }
        messages.error(request, "There was an error loading your email dashboard.")
    
    return render(request, "patient/email.html", context)

@patient_required
def compose_email(request):
    """
    View for composing and sending a new email.
    Uses EmailService for email composition and sending.
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
            
            # Send email via EmailService
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
    Uses direct model access since this is a simple read operation.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get message directly from model with ownership verification
        message = get_object_or_404(
            Message,
            id=message_id,
            recipient=patient.user
        )
        
        # Mark as read if it's unread
        if message.status == 'unread':
            message.status = 'read'
            message.save()
        
        # Format message using API serializer
        serializer = MessageSerializer(message)
        message_data = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'message': message_data,
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
    Uses direct model access for simple CRUD operations.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get message with ownership verification
        message = get_object_or_404(
            Message,
            id=message_id,
            recipient=patient.user
        )
        
        # Perform the requested action
        if action == 'mark_read':
            message.status = 'read'
            message.save()
            messages.success(request, "Email marked as read.")
        elif action == 'mark_unread':
            message.status = 'unread'
            message.save()
            messages.success(request, "Email marked as unread.")
        elif action == 'archive':
            message.status = 'archived'
            message.save()
            messages.success(request, "Email archived.")
        elif action == 'delete':
            message.status = 'deleted'
            message.save()
            messages.success(request, "Email deleted.")
        elif action == 'restore':
            message.status = 'read'  # Restore to read status
            message.save()
            messages.success(request, "Email restored.")
        else:
            messages.error(request, f"Unknown action: {action}")
            
    except Exception as e:
        logger.error(f"Error performing email action: {str(e)}")
        messages.error(request, f"Error performing action: {str(e)}")
    
    # Return to email dashboard
    return redirect('patient:patient_email')

@patient_required
def email_folder(request, folder):
    """
    View for displaying emails in a specific folder.
    Uses EmailService for folder-based email retrieval and AppointmentService for provider data.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        user = patient.user
        page = request.GET.get('page', 1)
        
        # Get emails for the specified folder using EmailService
        if folder == 'inbox':
            folder_data = EmailService.get_inbox_messages(patient.id, page=int(page))
        elif folder == 'sent':
            folder_data = EmailService.get_sent_messages(patient.id, page=int(page))
        else:
            # For archived and trash, use direct model access
            if folder == 'archived':
                folder_messages = Message.objects.filter(
                    recipient=user,
                    status='archived'
                ).order_by('-created_at')
            elif folder == 'trash':
                folder_messages = Message.objects.filter(
                    recipient=user,
                    status='deleted'
                ).order_by('-created_at')
            else:
                folder_messages = Message.objects.none()
            
            # Format messages using API serializer
            serializer = MessageSerializer(folder_messages, many=True)
            folder_data = {
                'success': True,
                'messages': serializer.data,
                'total_count': folder_messages.count()
            }
        
        # Get healthcare providers from AppointmentService - UPDATED
        provider_data = AppointmentService.get_patient_healthcare_providers(patient.id)
        
        # Format messages using API serializer if needed
        folder_messages = folder_data.get('messages', [])
        if hasattr(folder_messages, 'model'):
            serializer = MessageSerializer(folder_messages, many=True)
            folder_data['messages'] = serializer.data
        
        # Get counts for sidebar
        unread_count = Message.objects.filter(recipient=user, status='unread').count()
        read_count = Message.objects.filter(recipient=user, status='read').count()
        sent_count = Message.objects.filter(sender=user).count()
        archived_count = Message.objects.filter(recipient=user, status='archived').count()
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'messages': folder_data.get('messages', []),
            'folder': folder,
            'unread_count': unread_count,
            'read_count': read_count,
            'sent_count': sent_count,
            'archived_count': archived_count,
            'total_count': folder_data.get('total_count', 0),
            'providers': provider_data.get('healthcare_providers', []),  # FROM SERVICE
            'active_section': 'email'
        }
    except Exception as e:
        logger.error(f"Error retrieving folder emails: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'messages': [],
            'folder': folder,
            'unread_count': 0,
            'read_count': 0,
            'sent_count': 0,
            'archived_count': 0,
            'total_count': 0,
            'providers': [],  # Empty fallback
            'active_section': 'email'
        }
        messages.error(request, f"There was an error loading the {folder} folder.")
    
    return render(request, "patient/email_folder.html", context)
