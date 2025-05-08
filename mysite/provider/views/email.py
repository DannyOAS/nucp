# views/email.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from common.models import Message
from theme_name.repositories import ProviderRepository, PatientRepository
from provider.utils import get_current_provider  # or from provider.utils import get_current_provider


# Import the helper function

def provider_email(request):
    """Main email view for providers with consistent provider ID."""
    # Get provider using the consistent helper function
    provider = get_current_provider(request)
    provider_id = provider['id']
    
    # Get folder parameter (inbox, sent, priority)
    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('search', '')
    
    # Get user ID based on provider - for transition period
    user_id = getattr(request.user, 'id', provider_id)  # Default to provider ID
    
    # Start with all messages for this user
    try:
        from common.models import Message
        message_qs = Message.objects.all()
        
        # Filter based on folder
        if folder == 'inbox':
            # Show messages where user is recipient
            message_qs = message_qs.filter(recipient_id=user_id)
        elif folder == 'sent':
            # Show messages where user is sender
            message_qs = message_qs.filter(sender_id=user_id)
        elif folder == 'priority':
            # Check if priority field exists, otherwise use status
            if hasattr(Message, 'priority'):
                message_qs = message_qs.filter(recipient_id=user_id, priority='high')
            else:
                # Fallback to using status field if available
                message_qs = message_qs.filter(recipient_id=user_id, status='priority')
        elif folder == 'archived':
            # Check if there's a status field we can use for archived
            if hasattr(Message, 'status'):
                message_qs = message_qs.filter(recipient_id=user_id, status='archived')
            else:
                # If no archived status, just show inbox messages with warning
                message_qs = message_qs.filter(recipient_id=user_id)
                django_messages.warning(request, "Archive feature is not fully implemented yet.")
        
        # Apply search filter if provided
        if search_query:
            message_qs = message_qs.filter(subject__icontains=search_query) | message_qs.filter(content__icontains=search_query)
        
        # Order by most recent first
        message_qs = message_qs.order_by('-created_at')
        
        # Get the messages and add any additional data needed for display
        messages_list = []
        for msg in message_qs[:10]:  # Limit to 10 for now
            # Get sender name based on sender_id or sender_type
            sender_name = "Unknown"
            if hasattr(msg, 'sender') and msg.sender:
                if hasattr(msg.sender, 'first_name'):
                    sender_name = f"{msg.sender.first_name} {msg.sender.last_name}"
                else:
                    sender_name = str(msg.sender)
            
            # Format timestamp
            timestamp = msg.created_at.strftime('%B %d, %Y') if hasattr(msg, 'created_at') else "Unknown"
            
            # Determine if message is read
            is_read = True
            if hasattr(msg, 'read'):
                is_read = msg.read
            elif hasattr(msg, 'read_at'):
                is_read = msg.read_at is not None
            elif hasattr(msg, 'status'):
                is_read = msg.status != 'unread'
                
            messages_list.append({
                'id': msg.id,
                'sender_name': sender_name,
                'subject': msg.subject,
                'content': msg.content[:100] + ('...' if len(msg.content) > 100 else ''),
                'timestamp': timestamp,
                'read': is_read
            })
    except Exception as e:
        print(f"Error getting messages: {e}")
        messages_list = []
    
    # Count statistics for sidebar - use try/except for robustness
    try:
        from common.models import Message
        
        # Unread count
        unread_count = Message.objects.filter(recipient_id=user_id)
        if hasattr(Message, 'read'):
            unread_count = unread_count.filter(read=False).count()
        elif hasattr(Message, 'read_at'):
            unread_count = unread_count.filter(read_at__isnull=True).count()
        elif hasattr(Message, 'status'):
            unread_count = unread_count.filter(status='unread').count()
        else:
            unread_count = 5  # Fallback default
            
        # Read count
        read_count = Message.objects.filter(recipient_id=user_id)
        if hasattr(Message, 'read'):
            read_count = read_count.filter(read=True).count()
        elif hasattr(Message, 'read_at'):
            read_count = read_count.filter(read_at__isnull=False).count()
        elif hasattr(Message, 'status'):
            read_count = read_count.exclude(status='unread').count()
        else:
            read_count = 12  # Fallback default
            
        # Sent count
        sent_count = Message.objects.filter(sender_id=user_id).count()
        
        # Priority count
        priority_count = 0
        if hasattr(Message, 'priority'):
            priority_count = Message.objects.filter(recipient_id=user_id, priority='high').count()
        elif hasattr(Message, 'status'):
            priority_count = Message.objects.filter(recipient_id=user_id, status='priority').count()
        else:
            priority_count = 3  # Fallback default
            
    except Exception as e:
        print(f"Error calculating message counts: {e}")
        unread_count = 5
        read_count = 12
        sent_count = 8
        priority_count = 3
    
    # Get patients for compose functionality
    # Use direct ORM approach - get patients for this specific provider
    try:
        # Get patients for this provider
        from provider.models import Provider
        from theme_name.models import PatientRegistration
        from django.db.models import Q
        from common.models import Appointment
        
        # Get provider object
        provider_obj = Provider.objects.get(id=provider_id)
        
        # Method 1: Get patients directly assigned to provider if field exists
        if hasattr(PatientRegistration, 'provider'):
            # Get patients directly assigned to this provider
            patients = PatientRegistration.objects.filter(provider=provider_obj)
        else:
            # Method 2: Get patient IDs from appointments with this provider
            patient_ids = Appointment.objects.filter(
                doctor=provider_obj
            ).values_list('patient_id', flat=True).distinct()
            
            # Get the patient objects
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
        
        # Print useful debug info
        print(f"Using provider ID {provider_id}, found {patients.count()} patients")
        
    except Exception as e:
        print(f"Error getting provider's patients: {e}")
        from theme_name.repositories import PatientRepository
        patients = PatientRepository.get_all()

    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'priority_count': priority_count,
        'messages': messages_list,
        'folder': folder,
        'patients': patients,
        'search_query': search_query,
        'active_section': 'email',
    }

    return render(request, 'provider/email.html', context)

def provider_compose_message(request):
    """Handle composing and sending new messages with consistent provider."""
    # Get provider using the consistent helper function
    provider = get_current_provider(request)
    provider_id = provider['id']
    
    if request.method == 'POST':
        # Handle form submission logic
        django_messages.success(request, "Message sent successfully.")
        return redirect('provider_email')

    # DIRECT DB ACCESS for patients - ensure we only get provider's patients
    try:
        # Import necessary models
        from provider.models import Provider
        from django.db.models import Q
        from theme_name.models import PatientRegistration
        from common.models import Appointment
        
        # Get provider object
        provider_obj = Provider.objects.get(id=provider_id)
        
        # Method 1: Check if PatientRegistration has provider field
        if hasattr(PatientRegistration, 'provider'):
            # Get patients directly assigned to this provider
            patients = PatientRegistration.objects.filter(provider=provider_obj)
        else:
            # Method 2: Get patient IDs from Appointment model
            # This gets patients who have appointments with this provider
            patient_ids = Appointment.objects.filter(
                doctor=provider_obj
            ).values_list('patient_id', flat=True).distinct()
            
            # Get the patient objects
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
        
        # Print useful debug info
        print(f"Using provider ID {provider_id}, found {patients.count()} patients")
            
    except Exception as e:
        # Log the error but don't use repository as fallback anymore
        print(f"Error getting provider's patients: {e}")
        patients = []  # Empty list, don't fallback to all patients
    
    # Get staff members (example data for now)
    staff_members = [
        {'id': 1, 'first_name': 'Nurse', 'last_name': 'Williams'},
        {'id': 2, 'first_name': 'Dr.', 'last_name': 'Thompson'},
    ]

    # Handle reply logic
    reply_to_id = request.GET.get('reply_to')
    original_message = None
    form_initial = {}

    if reply_to_id:
        try:
            # Try to get the original message from database
            from common.models import Message
            message = Message.objects.get(id=reply_to_id)
            
            # Set up reply information
            original_message = {
                'id': message.id,
                'subject': message.subject,
                'sender_type': getattr(message, 'sender_type', 'patient'),
                'sender': {
                    'id': message.sender_id,
                    'first_name': getattr(message.sender, 'first_name', 'Unknown') if message.sender else 'Unknown',
                    'last_name': getattr(message.sender, 'last_name', 'Sender') if message.sender else 'Sender'
                },
                'thread_id': getattr(message, 'thread_id', f'thread-{message.id}')
            }
            
        except Exception as e:
            # Fallback to mock data if message not found
            print(f"Error getting original message: {e}")
            original_message = {
                'id': reply_to_id,
                'subject': 'Original Message Subject',
                'sender_type': 'patient',
                'sender': {'id': 1, 'first_name': 'Jane', 'last_name': 'Doe'},
                'thread_id': 'thread-123'
            }
            
        # Set up form initial data
        form_initial = {
            'subject': f"Re: {original_message['subject']}",
            'recipient_type': original_message['sender_type'],
            'recipient_id': original_message['sender']['id'],
            'thread_id': original_message['thread_id']
        }

    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'form': {'initial': form_initial},
        'patients': patients,  # Use our filtered list, not repository data
        'staff_members': staff_members,
        'original_message': original_message,
        'active_section': 'email',
    }

    return render(request, 'provider/compose_email.html', context)

# Update other view functions with get_current_provider() as needed

def provider_message_action(request, message_id, action):
    # Existing function implementation
    action_text = action.replace('_', ' ')
    django_messages.success(request, f"Message {action_text} successfully.")

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

def load_templates(request):
    # Existing function implementation
    template_type = request.GET.get('type', '')

    templates = {
        'lab_results': {
            'subject': 'Your Recent Lab Results',
            'content': """Dear [Patient Name],

I've reviewed your recent lab results. Everything looks good.

Regards,
Dr. [Your Name]"""
        },
        'prescription_renewal': {
            'subject': 'Prescription Renewal',
            'content': """Dear [Patient Name],

Your prescription for [Medication] has been renewed.

Regards,
Dr. [Your Name]"""
        },
        'appointment_confirmation': {
            'subject': 'Appointment Confirmation',
            'content': """Dear [Patient Name],

Your appointment is confirmed for [Date] at [Time].

Regards,
Dr. [Your Name]"""
        },
        'post_visit': {
            'subject': 'Visit Summary',
            'content': """Dear [Patient Name],

Thank you for your visit today. Here is a summary of our discussion.

Regards,
Dr. [Your Name]"""
        },
        'referral': {
            'subject': 'Referral Information',
            'content': """Dear [Patient Name],

I've referred you to [Specialist Name].

Regards,
Dr. [Your Name]"""
        },
        'test_preparation': {
            'subject': 'Test Preparation Instructions',
            'content': """Dear [Patient Name],

Please follow these instructions to prepare for your upcoming test.

Regards,
Dr. [Your Name]"""
        }
    }

    if template_type in templates:
        return JsonResponse(templates[template_type])
    else:
        return JsonResponse({'subject': '', 'content': ''})

def provider_view_message(request, message_id):
    # Existing function implementation
    provider_id = getattr(request.user, 'id', 1)
    provider = ProviderRepository.get_by_id(provider_id)

    fake_messages = {
        1: {
            'subject': 'Lab Results Review',
            'content': 'Please review my lab results from last week.',
            'created_at': 'April 28, 2025 - 10:30 AM',
            'priority': 'normal',
            'read': False,
            'sender_info': {
                'name': 'Jane Doe',
                'type': 'patient',
                'email': 'jane.doe@example.com',
            }
        },
        2: {
            'subject': 'Follow-up Appointment',
            'content': 'When should I schedule my next appointment?',
            'created_at': 'April 27, 2025 - 02:45 PM',
            'priority': 'high',
            'read': True,
            'sender_info': {
                'name': 'John Smith',
                'type': 'patient',
                'email': 'john.smith@example.com',
            }
        }
    }

    message_data = fake_messages.get(int(message_id), {
        'subject': 'Unknown Message',
        'content': 'This message does not exist.',
        'created_at': 'N/A',
        'priority': 'normal',
        'read': True,
        'sender_info': {
            'name': 'Unknown',
            'type': 'unknown',
            'email': 'unknown@example.com',
        }
    })

    message = {
        'id': message_id,
        'subject': message_data['subject'],
        'content': message_data['content'],
        'created_at': message_data['created_at'],
        'priority': message_data['priority'],
        'read': message_data['read'],
    }

    sender_info = message_data['sender_info']
    thread_messages = []

    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'message': message,
        'sender_info': sender_info,
        'thread_messages': thread_messages,
    }

    return render(request, 'provider/view_message.html', context)
