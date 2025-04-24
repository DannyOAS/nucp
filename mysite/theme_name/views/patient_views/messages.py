from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...repositories import PatientRepository, MessageRepository
from ...services import MessageService
from ...models import Message
from ...forms import PatientMessageForm

def email_view(request):
    """Email view (alias for messages)"""
    patient = PatientRepository.get_current(request)
    message_data = MessageService.get_message_dashboard(patient['id'])
    context = {
        **message_data, 
        'active_section': 'email',
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}"
    }
    return render(request, "patient/email.html", context)

def patient_messages(request):
    """View for patients to see their messages"""
    patient = PatientRepository.get_current(request)
    
    # Get counts for inbox stats
    unread_count = Message.objects.filter(recipient=request.user, status='unread').count()
    read_count = Message.objects.filter(recipient=request.user, status='read').count()
    sent_count = Message.objects.filter(sender=request.user).exclude(status='deleted').count()
    archived_count = Message.objects.filter(recipient=request.user, status='archived').count()
    
    # Get messages
    unread_messages = Message.objects.filter(recipient=request.user, status='unread')
    read_messages = Message.objects.filter(recipient=request.user, status='read')
    
    # Combined queryset for pagination
    all_messages = unread_messages.union(read_messages).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(all_messages, 10)  # Show 10 messages per page
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    # Split the page results back into unread and read for display
    page_unread = [msg for msg in messages_page if msg.status == 'unread']
    page_read = [msg for msg in messages_page if msg.status == 'read']
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'archived_count': archived_count,
        'unread_messages': page_unread,
        'read_messages': page_read,
        'page_obj': messages_page,
        'active_section': 'email'  # For highlighting in sidebar
    }
    
    return render(request, 'patient/patient_messages.html', context)

def patient_sent_messages(request):
    """View for patients to see messages they've sent"""
    patient = PatientRepository.get_current(request)
    
    # Get sent messages
    sent_messages = Message.objects.filter(sender=request.user).exclude(status='deleted')
    
    # Pagination
    paginator = Paginator(sent_messages, 10)
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'sent_messages': messages_page,
        'page_obj': messages_page,
        'folder': 'sent',
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_sent_messages.html', context)

def patient_archived_messages(request):
    """View for patients to see archived messages"""
    patient = PatientRepository.get_current(request)
    
    # Get archived messages
    archived_messages = Message.objects.filter(recipient=request.user, status='archived')
    
    # Pagination
    paginator = Paginator(archived_messages, 10)
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'archived_messages': messages_page,
        'page_obj': messages_page,
        'folder': 'archived',
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_archived_messages.html', context)

def patient_view_message(request, message_id):
    """View for patients to read a specific message"""
    patient = PatientRepository.get_current(request)
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    # Mark as read if unread
    if message.status == 'unread':
        message.mark_as_read()
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'message': message,
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_view_message.html', context)

def patient_compose_message(request):
    """View for patients to compose a new message"""
    patient = PatientRepository.get_current(request)
    
    if request.method == 'POST':
        form = PatientMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            
            # Determine the recipient based on recipient_type
            recipient_type = form.cleaned_data['recipient_type']
            
            # In a real implementation, we would have a mapping to actual users
            # For now, we'll use a placeholder approach
            from django.contrib.auth.models import User
            
            if recipient_type == 'provider':
                # Assign to the patient's provider
                # For mock implementation, just get the first staff user
                provider = User.objects.filter(is_staff=True).first()
                if provider:
                    message.recipient = provider
                else:
                    messages.error(request, "No provider found in the system.")
                    return redirect('patient_messages')
            elif recipient_type == 'pharmacy':
                # Assign to pharmacy user
                pharmacy_user = User.objects.filter(username='pharmacy').first()
                if pharmacy_user:
                    message.recipient = pharmacy_user
                else:
                    messages.error(request, "Pharmacy service not available.")
                    return redirect('patient_messages')
            elif recipient_type == 'billing':
                # Assign to billing department
                billing_user = User.objects.filter(username='billing').first()
                if billing_user:
                    message.recipient = billing_user
                else:
                    messages.error(request, "Billing department not available.")
                    return redirect('patient_messages')
            
            message.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('patient_messages')
    else:
        form = PatientMessageForm()
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'form': form,
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_compose_message.html', context)

def patient_message_action(request, message_id, action):
    """Handle message actions (mark read/unread, archive, delete)"""
    patient = PatientRepository.get_current(request)
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    if action == 'mark_read':
        message.mark_as_read()
        messages.success(request, "Message marked as read.")
    elif action == 'mark_unread':
        message.mark_as_unread()
        messages.success(request, "Message marked as unread.")
    elif action == 'archive':
        message.archive()
        messages.success(request, "Message archived.")
    elif action == 'delete':
        message.delete_message()
        messages.success(request, "Message deleted.")
    
    # Redirect based on the current folder
    referer = request.META.get('HTTP_REFERER', '')
    if 'archived' in referer:
        return redirect('patient_archived_messages')
    elif 'sent' in referer:
        return redirect('patient_sent_messages')
    else:
        return redirect('patient_messages')

def patient_search(request):
    """Search patient records"""
    patient = PatientRepository.get_current(request)
    query = request.GET.get('query', '')
    
    search_results = {}
    if query:
        # Use repository to search across patient data
        search_results = PatientRepository.search(patient['id'], query)
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'query': query,
        'results': search_results,
        'active_section': 'search'
    }
    
    return render(request, 'patient/search_results.html', context)
