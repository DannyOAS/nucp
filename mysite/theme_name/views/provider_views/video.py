from django.shortcuts import render
from ...repositories import ProviderRepository
from ...services import VideoService

def provider_video_consultation(request):
    """Provider video consultation view"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Setup video consultation
    video_data = VideoService.setup_provider_consultation(provider_id)
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'video_data': video_data,
        'active_section': 'consultations'
    }
    
    return render(request, "provider/video_consultation.html", context)
