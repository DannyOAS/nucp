# provider/views/profile.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import logging

from provider.services import ProviderService
from provider.utils import get_current_provider
from provider.forms import ProviderProfileEditForm

logger = logging.getLogger(__name__)

@login_required
def provider_profile(request):
    """Provider profile page with edit functionality using authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        form = ProviderProfileEditForm(request.POST, instance=provider)
        if form.is_valid():
            try:
                # Update profile using service
                result = ProviderService.update_provider_profile(
                    provider_id=provider.id,
                    form_data=form.cleaned_data,
                    user=provider.user
                )
                
                if result.get('success', False):
                    messages.success(request, "Profile updated successfully!")
                    # Update provider_dict for template with new values
                    provider_dict = result.get('provider_dict', provider_dict)
                else:
                    messages.error(request, result.get('error', "Error updating profile."))
            except Exception as e:
                logger.error(f"Error updating profile: {str(e)}")
                messages.error(request, f"Error updating profile: {str(e)}")
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Pre-fill form with existing provider data
        user = provider.user
        form = ProviderProfileEditForm(instance=provider, initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        })
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'profile',
        'form': form
    }
    return render(request, "provider/profile.html", context)

@login_required
def provider_settings(request):
    """Provider settings page with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process settings form
            settings_data = {
                'notification_email': request.POST.get('notification_email', provider.user.email),
                'sms_notifications': request.POST.get('sms_notifications') == 'on',
                'email_notifications': request.POST.get('email_notifications') == 'on',
                'default_appointment_duration': int(request.POST.get('default_appointment_duration', 30)),
                'calendar_sync_enabled': request.POST.get('calendar_sync_enabled') == 'on',
            }
            
            # Update settings using service
            result = ProviderService.update_provider_settings(
                provider_id=provider.id,
                settings_data=settings_data
            )
            
            if result.get('success', False):
                messages.success(request, "Settings updated successfully!")
            else:
                messages.error(request, result.get('error', "Error updating settings."))
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            messages.error(request, f"Error updating settings: {str(e)}")
    
    # Get current settings
    try:
        # Get settings from service
        settings_data = ProviderService.get_provider_settings(provider.id)
        settings = settings_data.get('settings', {
            'notification_email': getattr(provider, 'notification_email', provider.user.email),
            'sms_notifications': getattr(provider, 'sms_notifications', False),
            'email_notifications': getattr(provider, 'email_notifications', True),
            'default_appointment_duration': getattr(provider, 'default_appointment_duration', 30),
            'calendar_sync_enabled': getattr(provider, 'calendar_sync_enabled', False),
        })
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        settings = {
            'notification_email': getattr(provider, 'notification_email', provider.user.email),
            'sms_notifications': getattr(provider, 'sms_notifications', False),
            'email_notifications': getattr(provider, 'email_notifications', True),
            'default_appointment_duration': getattr(provider, 'default_appointment_duration', 30),
            'calendar_sync_enabled': getattr(provider, 'calendar_sync_enabled', False),
        }
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'settings',
        'settings': settings
    }
    return render(request, "provider/settings.html", context)

@login_required
def provider_help_support(request):
    """Provider help and support page with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get support data from service
        support_data = ProviderService.get_help_support_data()
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'help_support',
            'support_email': support_data.get('support_email', 'support@northernhealth.ca'),
            'support_phone': support_data.get('support_phone', '1-800-555-0100'),
            'faq_items': support_data.get('faq_items', [
                {
                    'question': 'How do I schedule a new appointment?',
                    'answer': 'Go to the Appointments section and click "Schedule Appointment". Then select a patient, date, and time.'
                },
                {
                    'question': 'How do I add a new patient?',
                    'answer': 'Go to the Patients section and click "Add Patient". Fill out the required information and submit the form.'
                },
                {
                    'question': 'How do I issue a new prescription?',
                    'answer': 'Go to the Prescriptions section and click "Create Prescription". Select a patient and enter the medication details.'
                },
                {
                    'question': 'How do I use the AI scribe feature?',
                    'answer': 'During a video consultation, click "Start Recording" to begin recording. After the session, the AI will generate clinical notes for review.'
                },
            ])
        }
    except Exception as e:
        logger.error(f"Error loading help and support data: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'help_support',
            'support_email': 'support@northernhealth.ca',
            'support_phone': '1-800-555-0100',
            'faq_items': [
                {
                    'question': 'How do I schedule a new appointment?',
                    'answer': 'Go to the Appointments section and click "Schedule Appointment". Then select a patient, date, and time.'
                },
                {
                    'question': 'How do I add a new patient?',
                    'answer': 'Go to the Patients section and click "Add Patient". Fill out the required information and submit the form.'
                },
                {
                    'question': 'How do I issue a new prescription?',
                    'answer': 'Go to the Prescriptions section and click "Create Prescription". Select a patient and enter the medication details.'
                },
                {
                    'question': 'How do I use the AI scribe feature?',
                    'answer': 'During a video consultation, click "Start Recording" to begin recording. After the session, the AI will generate clinical notes for review.'
                },
            ]
        }
    
    return render(request, "provider/help_support.html", context)
