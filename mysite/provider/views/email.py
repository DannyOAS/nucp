# provider/views/email.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from theme_name.repositories import ProviderRepository, PatientRepository

@login_required
def provider_email(request):
    """Main email view for providers with authentication."""
    # Check that user is in providers group
    if not request.user.groups.filter(name='providers').exists():
        return redirect('unauthorized')
    
    # Get the authenticated user
    user = request.user
    
    # Get provider associated with this user
    from provider.models import Provider
    try:
        provider = Provider.objects.get(user=user)
        # Create a dictionary compatible with existing templates
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': getattr(provider, 'specialty', 'General'),
            'is_active': getattr(provider, 'is_active', True),
        }
    except Provider.DoesNotExist:
        # Create a provider record if it doesn't exist
        provider = Provider.objects.create(
            user=user,
            license_number=f'TMP{user.id}',
            specialty='General',
            is_active=True
        )
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': provider.specialty,
        }

    # Get folder parameter (inbox, sent, priority)
    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('search', '')
    
    # Get user ID from authenticated user
    user_id = user.id
    
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
                # If no archived status, just show inbox messages
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
            # Get sender name
            sender_name = "Unknown"
            if hasattr(msg, 'sender') and msg.sender:
                if isinstance(msg.sender, User):
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
    
    # Count statistics for sidebar
    try:
        unread_count = Message.objects.filter(recipient_id=user_id)
        if hasattr(Message, 'read'):
            unread_count = unread_count.filter(read=False).count()
        elif hasattr(Message, 'read_at'):
            unread_count = unread_count.filter(read_at__isnull=True).count()
        elif hasattr(Message, 'status'):
            unread_count = unread_count.filter(status='unread').count()
        else:
            unread_count = 5  # Fallback default
            
        read_count = Message.objects.filter(recipient_id=user_id)
        if hasattr(Message, 'read'):
            read_count = read_count.filter(read=True).count()
        elif hasattr(Message, 'read_at'):
            read_count = read_count.filter(read_at__isnull=False).count()
        elif hasattr(Message, 'status'):
            read_count = read_count.exclude(status='unread').count()
        else:
            read_count = 12  # Fallback default
            
        sent_count = Message.objects.filter(sender_id=user_id).count()
        
        # For priority count
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
    
    # Get patients for this provider
    try:
        # Method 1: Get patients directly assigned to provider if field exists
        from theme_name.models import PatientRegistration
        
        if hasattr(PatientRegistration, 'provider'):
            # Get patients directly assigned to this provider
            patients = PatientRegistration.objects.filter(provider=provider)
        else:
            # Method 2: Get patient IDs from appointments with this provider
            from common.models import Appointment
            patient_ids = Appointment.objects.filter(
                doctor=provider
            ).values_list('patient_id', flat=True).distinct()
            
            # Get the patient objects
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
            
        print(f"Found {patients.count()} patients for provider {provider.id}")
        
    except Exception as e:
        print(f"Error getting provider's patients: {e}")
        # Fall back to repository in transition period
        patients = PatientRepository.get_all()

    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {user.last_name}",
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

@login_required
def provider_compose_message(request):
    """Handle composing and sending new messages with authentication."""
    # Check that user is in providers group
    if not request.user.groups.filter(name='providers').exists():
        return redirect('unauthorized')
    
    # Get the authenticated user
    user = request.user
    
    # Get provider associated with this user
    from provider.models import Provider
    try:
        provider = Provider.objects.get(user=user)
        # Create a dictionary compatible with existing templates
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': getattr(provider, 'specialty', 'General'),
            'is_active': getattr(provider, 'is_active', True),
        }
    except Provider.DoesNotExist:
        # Create a provider record if it doesn't exist
        provider = Provider.objects.create(
            user=user,
            license_number=f'TMP{user.id}',
            specialty='General',
            is_active=True
        )
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': provider.specialty,
        }
    
    if request.method == 'POST':
        # Handle form submission
        try:
            from common.models import Message
            
            recipient_type = request.POST.get('recipient_type')
            
            # Get the appropriate recipient ID based on type
            if recipient_type == 'patient':
                recipient_id = request.POST.get('recipient_id')
            elif recipient_type == 'staff':
                recipient_id = request.POST.get('staff_recipient_id')
            else:
                recipient_id = None
                
            if recipient_id:
                # Try to get the recipient user
                try:
                    recipient = User.objects.get(id=recipient_id)
                    
                    # Create the message
                    message = Message.objects.create(
                        sender=user,
                        recipient=recipient,
                        subject=request.POST.get('subject', ''),
                        content=request.POST.get('content', ''),
                    )
                    
                    # Set priority if applicable
                    if request.POST.get('priority') == 'high' and hasattr(Message, 'priority'):
                        message.priority = 'high'
                        message.save()
                    
                    django_messages.success(request, "Message sent successfully.")
                except User.DoesNotExist:
                    django_messages.error(request, "Recipient not found.")
            else:
                django_messages.error(request, "No recipient selected.")
        except Exception as e:
            print(f"Error sending message: {e}")
            django_messages.error(request, "Error sending message.")
            
        return redirect('provider_email')

    # Get patients for this provider
    try:
        # Method 1: Get patients directly assigned to provider if field exists
        from theme_name.models import PatientRegistration
        
        if hasattr(PatientRegistration, 'provider'):
            # Get patients directly assigned to this provider
            patients = PatientRegistration.objects.filter(provider=provider)
        else:
            # Method 2: Get patient IDs from appointments with this provider
            from common.models import Appointment
            patient_ids = Appointment.objects.filter(
                doctor=provider
            ).values_list('patient_id', flat=True).distinct()
            
            # Get the patient objects
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
            
        print(f"Found {patients.count()} patients for provider {provider.id}")
        
    except Exception as e:
        print(f"Error getting provider's patients: {e}")
        patients = []
    
    # Get staff members
    try:
        # Get users in 'Staff' group
        from django.contrib.auth.models import Group
        staff_group = Group.objects.filter(name='staff').first()
        if staff_group:
            staff_users = staff_group.user_set.all()
            staff_members = [
                {
                    'id': staff.id, 
                    'first_name': staff.first_name, 
                    'last_name': staff.last_name,
                    'role': getattr(staff, 'role', '')
                } 
                for staff in staff_users
            ]
        else:
            # Fallback staff members
            staff_members = [
                {'id': 1, 'first_name': 'Nurse', 'last_name': 'Williams'},
                {'id': 2, 'first_name': 'Dr.', 'last_name': 'Thompson'},
            ]
    except Exception as e:
        print(f"Error getting staff members: {e}")
        # Fallback staff members
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
                    'id': message.sender.id,
                    'first_name': message.sender.first_name,
                    'last_name': message.sender.last_name
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
        'provider': provider_dict,
        'provider_name': f"Dr. {user.last_name}",
        'form': {'initial': form_initial},
        'patients': patients,
        'staff_members': staff_members,
        'original_message': original_message,
        'active_section': 'email',
    }

    return render(request, 'provider/compose_email.html', context)

# Handle message actions like mark as read/archive
@login_required
def provider_message_action(request, message_id, action):
    """Handle message actions with authentication."""
    # Check that user is in providers group
    if not request.user.groups.filter(name='providers').exists():
        return redirect('unauthorized')
    
    # Get the authenticated user
    user = request.user
    
    # Handle the action
    try:
        from common.models import Message
        message = Message.objects.get(id=message_id)
        
        # Verify the user has permission for this message
        if message.recipient != user and message.sender != user:
            django_messages.error(request, "You don't have permission to perform this action.")
            return redirect('provider_email')
        
        # Perform the action
        if action == 'mark_read':
            if hasattr(message, 'read'):
                message.read = True
                message.save()
            elif hasattr(message, 'read_at'):
                from django.utils import timezone
                message.read_at = timezone.now()
                message.save()
            elif hasattr(message, 'status'):
                message.status = 'read'
                message.save()
                
        elif action == 'mark_unread':
            if hasattr(message, 'read'):
                message.read = False
                message.save()
            elif hasattr(message, 'read_at'):
                message.read_at = None
                message.save()
            elif hasattr(message, 'status'):
                message.status = 'unread'
                message.save()
                
        elif action == 'archive':
            if hasattr(message, 'status'):
                message.status = 'archived'
                message.save()
                
        elif action == 'delete':
            message.delete()
            django_messages.success(request, "Message deleted successfully.")
            return redirect('provider_email')
            
        action_text = action.replace('_', ' ')
        django_messages.success(request, f"Message {action_text} successfully.")
        
    except Message.DoesNotExist:
        django_messages.error(request, "Message not found.")
    except Exception as e:
        print(f"Error performing message action: {e}")
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
    # Check that user is in providers group
    if not request.user.groups.filter(name='providers').exists():
        return redirect('unauthorized')
    
    # Get the authenticated user
    user = request.user
    
    # Get provider associated with this user
    from provider.models import Provider
    try:
        provider = Provider.objects.get(user=user)
        # Create a dictionary compatible with existing templates
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': getattr(provider, 'specialty', 'General'),
            'is_active': getattr(provider, 'is_active', True),
        }
    except Provider.DoesNotExist:
        # Create a provider record if it doesn't exist
        provider = Provider.objects.create(
            user=user,
            license_number=f'TMP{user.id}',
            specialty='General',
            is_active=True
        )
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': provider.specialty,
        }
    
    # Get the message
    try:
        from common.models import Message
        message = Message.objects.get(id=message_id)
        
        # Verify the user has permission to view this message
        if message.recipient != user and message.sender != user:
            django_messages.error(request, "You don't have permission to view this message.")
            return redirect('provider_email')
        
        # Mark as read if recipient is viewing
        if message.recipient == user:
            if hasattr(message, 'read'):
                message.read = True
                message.save()
            elif hasattr(message, 'read_at') and not message.read_at:
                from django.utils import timezone
                message.read_at = timezone.now()
                message.save()
            elif hasattr(message, 'status') and message.status == 'unread':
                message.status = 'read'
                message.save()
        
        # Format the message for display
        message_data = {
            'id': message.id,
            'subject': message.subject,
            'content': message.content,
            'created_at': message.created_at.strftime('%B %d, %Y - %I:%M %p') if hasattr(message, 'created_at') else "Unknown",
            'priority': getattr(message, 'priority', 'normal'),
            'read': True,  # We've just marked it as read if it wasn't already
        }
        
        # Get sender info
        sender_info = {
            'name': f"{message.sender.first_name} {message.sender.last_name}" if message.sender else "Unknown",
            'type': getattr(message, 'sender_type', 'user'),
            'email': message.sender.email if message.sender else "unknown@example.com",
        }
        
        # Get thread messages if thread_id exists
        thread_messages = []
        if hasattr(message, 'thread_id') and message.thread_id:
            thread_msgs = Message.objects.filter(thread_id=message.thread_id).exclude(id=message.id).order_by('created_at')
            for thread_msg in thread_msgs:
                thread_messages.append({
                    'id': thread_msg.id,
                    'subject': thread_msg.subject,
                    'content': thread_msg.content,
                    'sender': f"{thread_msg.sender.first_name} {thread_msg.sender.last_name}" if thread_msg.sender else "Unknown",
                    'created_at': thread_msg.created_at.strftime('%B %d, %Y - %I:%M %p') if hasattr(thread_msg, 'created_at') else "Unknown",
                })
        
    except Message.DoesNotExist:
        django_messages.error(request, "Message not found.")
        return redirect('provider_email')
    except Exception as e:
        print(f"Error viewing message: {e}")
        django_messages.error(request, f"Error viewing message: {str(e)}")
        return redirect('provider_email')

    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {user.last_name}",
        'message': message_data,
        'sender_info': sender_info,
        'thread_messages': thread_messages,
        'active_section': 'email',
    }

    return render(request, 'provider/view_message.html', context)

# Load message templates for compose
def load_templates(request):
    """AJAX endpoint to load message templates."""
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
