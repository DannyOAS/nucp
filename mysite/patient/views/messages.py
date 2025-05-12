# patient/views/messages.py
from patient.decorators import patient_required
from common.models import Message
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages

@patient_required
def patient_messages(request):
    """Patient inbox view"""
    patient = request.patient
    
    messages = Message.objects.filter(
        recipient=request.user
    ).exclude(
        status='deleted'
    ).order_by('-created_at')
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'messages': messages,
        'active_section': 'messages'
    }
    
    return render(request, "patient/messages.html", context)

@patient_required
def patient_compose_message(request):
    """Compose new message"""
    patient = request.patient
    
    if request.method == 'POST':
        # Handle message creation
        subject = request.POST.get('subject')
        content = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type')
        
        # Determine recipient based on type
        recipient = None
        if recipient_type == 'provider' and patient.primary_provider:
            recipient = patient.primary_provider.user
        elif recipient_type == 'pharmacy':
            # You might need to implement pharmacy user lookup
            pass
        elif recipient_type == 'billing':
            # You might need to implement billing department user lookup
            pass
        
        if recipient:
            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                content=content,
                status='unread'
            )
            django_messages.success(request, "Message sent successfully!")
            return redirect('patient:patient_messages')
        else:
            django_messages.error(request, "Could not determine recipient. Please try again.")
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'active_section': 'messages'
    }
    
    return render(request, "patient/compose_message.html", context)
