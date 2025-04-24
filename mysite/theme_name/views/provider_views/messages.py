from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...models import Message
from ...forms import ProviderMessageForm

def provider_messages(request):
    """Provider messages view"""
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
    paginator = Paginator(all_messages, 10)
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
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'archived_count': archived_count,
        'unread_messages': page_unread,
        'read_messages': page_read,
        'page_obj': messages_page,
        'active_section': 'messages'  # For highlighting in sidebar
    }
    
    return render(request, 'provider/provider_messages.html', context)

def provider_sent_messages(request):
    """View for providers to see messages they've sent"""
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
        'sent_messages': messages_page,
        'page_obj': messages_page,
        'folder': 'sent',
        'active_section': 'messages'
    }
    
    return render(request, 'provider/provider_sent_messages.html', context)

def provider_view_message(request, message_id):
    """View for providers to read a specific message"""
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    # Mark as read if unread
    if message.status == 'unread':
        message.mark_as_read()
    
    context = {
        'message': message,
        'active_section': 'messages'
    }
    
    return render(request, 'provider/provider_view_message.html', context)

def provider_compose_message(request):
    """View for providers to compose a new message"""
    if request.method == 'POST':
        form = ProviderMessageForm(request.POST, provider=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient_type = 'patient'  # Since provider is sending to patient
            message.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('provider_messages')
    else:
        form = ProviderMessageForm(provider=request.user)
    
    context = {
        'form': form,
        'active_section': 'messages'
    }
    
    return render(request, 'provider/provider_compose_message.html', context)

def provider_message_action(request, message_id, action):
    """Handle message actions (mark read/unread, archive, delete)"""
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
        return redirect('provider_archived_messages')
    elif 'sent' in referer:
        return redirect('provider_sent_messages')
    else:
        return redirect('provider_messages')
