# provider/views/email.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
import logging

from provider.services import MessageService
from provider.utils import get_current_provider
from api.v1.provider.serializers import MessageSerializer

logger = logging.getLogger(__name__)

@login_required
def provider_email(request):
    """Main email view for providers with authentication."""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')

    # Get folder parameter (inbox, sent, priority)
    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('search', '')
    
    try:
        # Get email data from service
        email_data = MessageService.get_provider_emails(
            provider_id=provider.id,
            user_id=request.user.id,
            folder=folder,
            search_query=search_query
        )
        
        # Format messages using API serializer if needed
        messages_list = email_data.get('messages', [])
        if hasattr(messages_list, 'model'):
            serializer = MessageSerializer(messages_list, many=True)
            email_data['messages'] = serializer.data
        
        # Get patients for this provider for compose functionality
        patients = MessageService.get_provider_patients(provider.id)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'unread_count': email_data.get('unread_count', 0),
            'read_count': email_data.get('read_count', 0),
            'sent_count': email_data.get('sent_count', 0),
            'priority_count': email_data.get('priority_count', 0),
            'messages': email_data.get('messages', []),
            'folder': folder,
            'patients': patients,
            'search_query': search_query,
            'active_section': 'email',
        }
    except Exception as e:
        logger.error(f"Error getting email data: {e}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'unread_count': 0,
            'read_count': 0,
            'sent_count': 0,
            'priority_count': 0,
            'messages': [],
            'folder': folder,
            'patients': [],
            'search_query': search_query,
            'active_section': 'email',
        }

    return render(request, 'provider/email.html', context)

@login_required
def provider_compose_message(request):
    """Handle composing and sending new messages with authentication."""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process form data
            message_data = {
                'recipient_type': request.POST.get('recipient_type'),
                'recipient_id': request.POST.get('recipient_id') or request.POST.get('staff_recipient_id'),
                'subject': request.POST.get('subject', ''),
                'content': request.POST.get('content', ''),
                'priority': request.POST.get('priority', 'normal'),
                'thread_id': request.POST.get('thread_id', None),
                'attachments': request.FILES.getlist('attachments') if 'attachments' in request.FILES else []
            }
            
            # Send message using service
            result = MessageService.send_provider_message(
                message_data=message_data,
                provider_id=provider.id,
                user=request.user
            )
            
            if result.get('success', False):
                django_messages.success(request, "Message sent successfully.")
                return redirect('provider_email')
            else:
                django_messages.error(request, result.get('error', "Error sending message."))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            django_messages.error(request, f"Error sending message: {str(e)}")
            
        return redirect('provider_email')

    # For GET requests, prepare the compose form
    try:
        # Get compose data from service
        compose_data = MessageService.get_compose_data(
            provider_id=provider.id,
            reply_to_id=request.GET.get('reply_to')
        )
        
        # Format original message with serializer if needed
        original_message = compose_data.get('original_message')
        if original_message and hasattr(original_message, '__dict__'):
            serializer = MessageSerializer(original_message)
            compose_data['original_message'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'form': {'initial': compose_data.get('form_initial', {})},
            'patients': compose_data.get('patients', []),
            'staff_members': compose_data.get('staff_members', []),
            'original_message': compose_data.get('original_message'),
            'active_section': 'email',
        }
    except Exception as e:
        logger.error(f"Error preparing compose form: {e}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'form': {'initial': {}},
            'patients': [],
            'staff_members': [],
            'active_section': 'email',
        }
    
    return render(request, 'provider/compose_email.html', context)

@login_required
def provider_message_action(request, message_id, action):
    """Handle message actions with authentication."""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Perform message action using service
        result = MessageService.perform_message_action(
            message_id=message_id,
            action=action,
            user=request.user
        )
        
        if result.get('success', False):
            action_text = action.replace('_', ' ')
            django_messages.success(request, f"Message {action_text} successfully.")
        else:
            django_messages.error(request, result.get('error', f"Error performing {action} action."))
    except Exception as e:
        logger.error(f"Error performing message action: {e}")
        django_messages.error(request, f"Error performing action: {str(e)}")

    # Determine redirect based on referring URL
    referer = request.META.get('HTTP_REFERER', '')
    if '/view/' in referer:
        return redirect('provider_view_message', message_id=message_id)
    elif 'folder=sent' in referer:
        return HttpResponseRedirect('/provider-dashboard/email/?folder=sent')
    elif 'folder=archived' in referer:
        return HttpResponseRedirect('/provider-dashboard/email/?folder=archived')
    elif 'folder=priority' in referer:
        return HttpResponseRedirect('/provider-dashboard/email/?folder=priority')
    else:
        return redirect('provider_email')

@login_required
def provider_view_message(request, message_id):
    """View a specific message with authentication."""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get message details using service
        message_data = MessageService.get_message_details(
            message_id=message_id,
            user=request.user
        )
        
        if not message_data.get('success', False):
            django_messages.error(request, message_data.get('error', "Message not found."))
            return redirect('provider_email')
        
        # Format message and thread messages with serializer if needed
        message = message_data.get('message')
        if message and hasattr(message, '__dict__'):
            serializer = MessageSerializer(message)
            message_data['message'] = serializer.data
        
        thread_messages = message_data.get('thread_messages', [])
        if hasattr(thread_messages, 'model'):
            serializer = MessageSerializer(thread_messages, many=True)
            message_data['thread_messages'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'message': message_data.get('message'),
            'sender_info': message_data.get('sender_info'),
            'thread_messages': message_data.get('thread_messages', []),
            'active_section': 'email',
        }
    except Exception as e:
        logger.error(f"Error viewing message: {e}")
        django_messages.error(request, f"Error viewing message: {str(e)}")
        return redirect('provider_email')

    return render(request, 'provider/view_message.html', context)

# Load message templates for compose
def load_templates(request):
    """AJAX endpoint to load message templates."""
    template_type = request.GET.get('type', '')
    
    try:
        # Get templates from service
        templates = MessageService.get_message_templates(template_type)
        return JsonResponse(templates)
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        return JsonResponse({'subject': '', 'content': ''})
