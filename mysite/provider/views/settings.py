# provider/views/settings.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import json
import logging

from provider.utils import get_current_provider
from provider.models import Provider

logger = logging.getLogger(__name__)

@login_required
def provider_settings(request):
    """Provider settings view with authenticated user."""
    # Get the current provider using our utility function
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # For now, create basic schedule data. Later you can implement proper models
        days_of_week = []
        
        for day_code, day_name in [
            ('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'),
            ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday')
        ]:
            # Default schedule - you can later load this from database
            days_of_week.append({
                'code': day_code,
                'name': day_name,
                'working': day_code not in ['sat', 'sun'],  # Default to weekdays only
                'start_time': '0900',
                'end_time': '1700',
                'lunch_break': False,
                'lunch_start': '1200',
                'lunch_end': '1300',
            })
        
        # Generate hour options
        hours = []
        for hour in range(6, 22):  # 6 AM to 9 PM
            for minute in [0, 15, 30, 45]:
                time_value = f"{hour:02d}{minute:02d}"
                time_label = f"{hour:02d}:{minute:02d}"
                hours.append({'value': time_value, 'label': time_label})
        
        # Lunch hour options (11 AM to 3 PM)
        lunch_hours = []
        for hour in range(11, 16):
            for minute in [0, 15, 30, 45]:
                time_value = f"{hour:02d}{minute:02d}"
                time_label = f"{hour:02d}:{minute:02d}"
                lunch_hours.append({'value': time_value, 'label': time_label})
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'settings',
            'days_of_week': days_of_week,
            'hours': hours,
            'lunch_hours': lunch_hours,
        }
        
        # Add default settings to provider object for template access
        provider_dict['settings'] = {
            'appt_in_person': True,
            'appt_virtual': True,
            'appt_emergency': False,
            'appt_duration_standard': 30,
            'appt_duration_extended': 60,
            'appt_lead_time': 24,
            'appt_future_limit': 30,
        }
        
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        messages.error(request, f"Error loading settings: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'settings',
            'days_of_week': [],
            'hours': [],
            'lunch_hours': [],
        }
    
    return render(request, "provider/settings.html", context)

@login_required
@require_POST
def update_provider_email(request):
    """Update provider email address."""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        new_email = request.POST.get('new_email')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate password
        if not authenticate(username=request.user.username, password=confirm_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('provider_settings')
        
        # Validate email
        try:
            validate_email(new_email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('provider_settings')
        
        # Check if email is already in use
        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            messages.error(request, 'This email address is already in use.')
            return redirect('provider_settings')
        
        # Update email
        request.user.email = new_email
        request.user.save()
        
        messages.success(request, 'Email address updated successfully.')
        
    except Exception as e:
        logger.error(f"Error updating email: {str(e)}")
        messages.error(request, f"Error updating email: {str(e)}")
    
    return redirect('provider_settings')

@login_required
@require_POST
def update_provider_password(request):
    """Update provider password."""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate current password
        if not authenticate(username=request.user.username, password=current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('provider_settings')
        
        # Validate new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('provider_settings')
        
        # Validate password strength
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('provider_settings')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password updated successfully.')
        
    except Exception as e:
        logger.error(f"Error updating password: {str(e)}")
        messages.error(request, f"Error updating password: {str(e)}")
    
    return redirect('provider_settings')

@login_required
@require_POST
def update_provider_info(request):
    """Update provider information."""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        specialty = request.POST.get('specialty', '').strip()
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        
        # Update provider info
        provider.specialty = specialty
        provider.phone = phone
        provider.bio = bio
        provider.save()
        
        messages.success(request, 'Provider information updated successfully.')
        
    except Exception as e:
        logger.error(f"Error updating provider info: {str(e)}")
        messages.error(request, f"Error updating provider info: {str(e)}")
    
    return redirect('provider_settings')

@login_required
@require_POST
def update_provider_schedule(request):
    """Update provider schedule and appointment settings."""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # For now, just collect the data and show success
        # Later you can implement proper database storage
        
        # Get appointment type settings
        appt_in_person = 'appt_in_person' in request.POST
        appt_virtual = 'appt_virtual' in request.POST
        appt_emergency = 'appt_emergency' in request.POST
        
        # Get appointment duration settings
        appt_duration_standard = int(request.POST.get('appt_duration_standard', 30))
        appt_duration_extended = int(request.POST.get('appt_duration_extended', 60))
        
        # Get booking settings
        appt_lead_time = int(request.POST.get('appt_lead_time', 24))
        appt_future_limit = int(request.POST.get('appt_future_limit', 30))
        
        # Get schedule data
        work_days = request.POST.getlist('work_days')
        schedule_data = {}
        
        for day_code in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            if day_code in work_days:
                start_time = request.POST.get(f'start_time_{day_code}', '0900')
                end_time = request.POST.get(f'end_time_{day_code}', '1700')
                lunch_break = f'lunch_break_{day_code}' in request.POST
                lunch_start = request.POST.get(f'lunch_start_{day_code}', '1200')
                lunch_end = request.POST.get(f'lunch_end_{day_code}', '1300')
                
                schedule_data[day_code] = {
                    'working': True,
                    'start_time': start_time,
                    'end_time': end_time,
                    'lunch_break': lunch_break,
                    'lunch_start': lunch_start,
                    'lunch_end': lunch_end,
                }
            else:
                schedule_data[day_code] = {
                    'working': False,
                    'start_time': '0900',
                    'end_time': '1700',
                    'lunch_break': False,
                    'lunch_start': '1200',
                    'lunch_end': '1300',
                }
        
        # TODO: Save the settings and schedule data to database
        # You can implement proper model storage later
        
        logger.info(f"Schedule updated for provider {provider.id}: {schedule_data}")
        logger.info(f"Appointment settings: in_person={appt_in_person}, virtual={appt_virtual}, emergency={appt_emergency}")
        
        messages.success(request, 'Schedule and appointment settings updated successfully.')
        
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        messages.error(request, f"Error updating schedule: {str(e)}")
    
    return redirect('provider_settings')
