from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging

from common.services import VideoService
from theme_name.data_access import get_provider_appointments
from provider.utils import get_current_provider

logger = logging.getLogger(__name__)

@login_required
def provider_video_consultation(request):
    """Video consultation view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get appointments for this provider
        all_appointments = get_provider_appointments(provider.id)
        
        # Filter for virtual appointments
        video_appointments = [a for a in all_appointments if a.get('type') == 'Virtual']
        
        # Get any active video sessions
        active_sessions = []
        try:
            if 'get_active_sessions' in dir(VideoService):
                active_sessions = VideoService.get_active_sessions(provider.id)
        except Exception as e:
            logger.error(f"Error retrieving active video sessions: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving video appointments: {str(e)}")
        video_appointments = []
        active_sessions = []
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'consultations',
        'video_appointments': video_appointments,
        'active_sessions': active_sessions
    }
    
    return render(request, 'provider/video_consultation.html', context)
