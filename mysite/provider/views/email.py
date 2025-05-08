# Update your email.py views file to properly handle anonymous users

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
#from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from theme_name.repositories import ProviderRepository, PatientRepository

from django.shortcuts import render, redirect
from django.contrib import messages as django_messages
# from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from theme_name.repositories import ProviderRepository, PatientRepository

# Inbox View
def provider_email(request):
    """Main email view for providers using mock data."""

    provider_id = getattr(request.user, 'id', 1)
    provider = ProviderRepository.get_by_id(provider_id)

    unread_count = 5
    read_count = 12
    sent_count = 8
    priority_count = 3

    folder = request.GET.get('folder', 'inbox')
    search_query = request.GET.get('search', '')

    messages_list = [
        {'id': 1, 'subject': 'Lab Results Review', 'sender_name': 'Jane Doe', 'timestamp': 'April 28, 2025', 'content': 'Please review my lab results.', 'read': False},
        {'id': 2, 'subject': 'Follow-up Appointment', 'sender_name': 'John Smith', 'timestamp': 'April 27, 2025', 'content': 'When should I book?', 'read': True},
    ]
    messages_list = [
        {
            'id': 1,
            'sender_name': 'Jane Doe',
            'subject': 'Lab Results Review',
            'timestamp': 'April 28, 2025',
            'content': 'Please review my lab results.',
            'read': False,
        },
        {
            'id': 2,
            'sender_name': 'John Smith',
            'subject': 'Follow-up Appointment',
            'timestamp': 'April 27, 2025',
            'content': 'When should I book?',
            'read': True,
        },
    ]


    patients = PatientRepository.get_all()

    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'priority_count': priority_count,
        'messages': messages_list,
        'page_obj': None,
        'folder': folder,
        'patients': patients,
        'search_query': search_query,
        'active_section': 'email',
    }

    return render(request, 'provider/view_email.html', context)

# Compose Message View
def provider_compose_message(request):
    """Handle composing and sending new messages (mock)."""

    provider_id = getattr(request.user, 'id', 1)
    provider = ProviderRepository.get_by_id(provider_id)

    if request.method == 'POST':
        django_messages.success(request, "Message sent successfully.")
        return redirect('provider_email')

    patients = PatientRepository.get_all()

    staff_members = [
        {'id': 1, 'first_name': 'Nurse', 'last_name': 'Williams'},
        {'id': 2, 'first_name': 'Dr.', 'last_name': 'Thompson'},
    ]

    reply_to_id = request.GET.get('reply_to')
    original_message = None
    form_initial = {}

    if reply_to_id:
        original_message = {
            'id': reply_to_id,
            'subject': 'Original Message Subject',
            'sender_type': 'patient',
            'sender': {'id': 1, 'first_name': 'Jane', 'last_name': 'Doe'},
            'thread_id': 'thread-123'
        }
        form_initial = {
            'subject': f"Re: {original_message['subject']}",
            'recipient_type': original_message['sender_type'],
            'recipient_id': original_message['sender']['id'],
            'thread_id': original_message['thread_id']
        }

    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.last_name}",
        'form': {'initial': form_initial},
        'patients': patients,
        'staff_members': staff_members,
        'original_message': original_message,
        'active_section': 'email',
    }

    return render(request, 'provider/compose_email.html', context)

# Handle Actions like Mark as Read / Archive
def provider_message_action(request, message_id, action):
    """Handle message actions (mock)."""

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

# Load Message Templates for Compose
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

# View a single Message
def provider_view_message(request, message_id):
    """View a specific message (mock)."""

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
        'provider_name': f"Dr. {provider.first_name} {provider.last_name}",
        'message': message,
        'sender_info': sender_info,
        'thread_messages': thread_messages,
    }

    return render(request, 'provider/view_message.html', context)
