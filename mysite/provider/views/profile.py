from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
# from django.contrib.auth.decorators import login_required

from provider.models import Provider
from provider.forms import ProviderProfileForm
from .dashboard import get_provider

# @login_required
def provider_profile(request):
    """Provider profile page with edit functionality"""
    provider = get_provider(request)
    
    if request.method == 'POST':
        form = ProviderProfileForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('provider_profile')
        else:
            messages.error(request, "There was an error updating your profile. Please check the form.")
    else:
        # Pre-fill form with existing provider data
        form = ProviderProfileForm(instance=provider)
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'active_section': 'profile',
        'form': form
    }
    return render(request, "provider/profile.html", context)

# @login_required
def provider_settings(request):
    """Provider settings page"""
    provider = get_provider(request)
    
    # Get notification preferences (mock data for now)
    notification_preferences = {
        'email_notifications': True,
        'sms_notifications': False,
        'appointment_reminders': True,
        'prescription_alerts': True,
        'lab_result_alerts': True
    }
    
    # Get display preferences (mock data for now)
    display_preferences = {
        'theme': 'default',
        'calendar_view': 'week',
        'start_page': 'dashboard',
        'items_per_page': 10
    }
    
    if request.method == 'POST':
        # Update notification preferences
        notification_preferences['email_notifications'] = 'email_notifications' in request.POST
        notification_preferences['sms_notifications'] = 'sms_notifications' in request.POST
        notification_preferences['appointment_reminders'] = 'appointment_reminders' in request.POST
        notification_preferences['prescription_alerts'] = 'prescription_alerts' in request.POST
        notification_preferences['lab_result_alerts'] = 'lab_result_alerts' in request.POST
        
        # Update display preferences
        display_preferences['theme'] = request.POST.get('theme', 'default')
        display_preferences['calendar_view'] = request.POST.get('calendar_view', 'week')
        display_preferences['start_page'] = request.POST.get('start_page', 'dashboard')
        display_preferences['items_per_page'] = int(request.POST.get('items_per_page', 10))
        
        # In a real implementation, save these preferences to the database
        
        messages.success(request, "Settings updated successfully!")
        return redirect('provider_settings')
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'active_section': 'settings',
        'notification_preferences': notification_preferences,
        'display_preferences': display_preferences
    }
    return render(request, "provider/settings.html", context)

# @login_required
def provider_help_support(request):
    """Provider help and support page"""
    provider = get_provider(request)
    
    # Mock FAQ data
    faqs = [
        {
            'question': 'How do I schedule a new appointment?',
            'answer': 'To schedule a new appointment, navigate to the Appointments section and click on "Schedule New Appointment". Fill in the required details and click Save.'
        },
        {
            'question': 'How do I approve a prescription request?',
            'answer': 'Prescription requests can be found in the Prescriptions section. Click on "Review" next to the request you want to approve, verify the details, and click the "Approve" button.'
        },
        {
            'question': 'Can I customize my dashboard?',
            'answer': 'Yes, you can customize your dashboard by going to Settings and adjusting the display preferences.'
        },
        {
            'question': 'How do I use the AI Scribe feature?',
            'answer': 'During a video consultation, click on the "Start Recording" button to begin using AI Scribe. After the appointment, you\'ll be able to view and edit the generated clinical notes.'
        },
        {
            'question': 'How do I contact technical support?',
            'answer': 'For technical support, please email support@example.com or call our help desk at (555) 123-4567.'
        }
    ]
    
    # Mock support contact information
    support_contacts = {
        'email': 'support@example.com',
        'phone': '(555) 123-4567',
        'hours': 'Monday to Friday, 9 AM - 5 PM EST'
    }
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'active_section': 'help_support',
        'faqs': faqs,
        'support_contacts': support_contacts
    }
    return render(request, "provider/help_support.html", context)
