# provider/views/profile.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
import logging
import requests

from provider.forms import ProviderProfileEditForm
from provider.utils import get_current_provider

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
                # Get cleaned data from form
                updated_data = form.cleaned_data
                
                # Update user data
                user = provider.user
                if 'first_name' in updated_data:
                    user.first_name = updated_data.get('first_name')
                if 'last_name' in updated_data:
                    user.last_name = updated_data.get('last_name')
                if 'email' in updated_data:
                    user.email = updated_data.get('email')
                user.save()
                
                # Update provider data 
                provider = form.save()
                
                # API version (commented out for now):
                # api_url = request.build_absolute_uri(f'/api/provider/profile/{provider.id}/')
                # data = {
                #     'user': {
                #         'first_name': updated_data.get('first_name'),
                #         'last_name': updated_data.get('last_name'),
                #         'email': updated_data.get('email')
                #     },
                #     'specialty': updated_data.get('specialty'),
                #     'bio': updated_data.get('bio'),
                #     'phone': updated_data.get('phone'),
                #     'license_number': updated_data.get('license_number')
                # }
                # response = requests.put(api_url, json=data)
                # if response.status_code == 200:
                #     provider_dict = response.json()
                # else:
                #     # Handle error
                #     messages.error(request, "Error updating profile via API")
                
                # Update provider_dict for template
                provider_dict = {
                    'id': provider.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'specialty': provider.specialty,
                    'is_active': provider.is_active,
                }
                
                # Add success message
                messages.success(request, "Profile updated successfully!")
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
    
    # Handle settings form submission
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
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/provider/profile/{provider.id}/')
            # response = requests.patch(api_url, json=settings_data)
            # if response.status_code == 200:
            #     messages.success(request, "Settings updated successfully!")
            # else:
            #     messages.error(request, "Error updating settings via API")
            
            # Save settings to provider
            for key, value in settings_data.items():
                if hasattr(provider, key):
                    setattr(provider, key, value)
            
            provider.save()
            messages.success(request, "Settings updated successfully!")
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            messages.error(request, f"Error updating settings: {str(e)}")
    
    # Get current settings
    try:
        settings = {
            'notification_email': getattr(provider, 'notification_email', provider.user.email),
            'sms_notifications': getattr(provider, 'sms_notifications', False),
            'email_notifications': getattr(provider, 'email_notifications', True),
            'default_appointment_duration': getattr(provider, 'default_appointment_duration', 30),
            'calendar_sync_enabled': getattr(provider, 'calendar_sync_enabled', False),
        }
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        settings = {}
    
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
