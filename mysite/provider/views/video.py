from django.shortcuts import render
from theme_name.repositories import ProviderRepository
from common.services import VideoService
from theme_name.data_access import get_provider_appointments


def provider_video_consultation(request):
    provider_id = 1
    all_appointments = get_provider_appointments(provider_id)
    video_appointments = [a for a in all_appointments if a.get('type') == 'Virtual']
    context = {
        'active_section': 'consultations',
        'provider_name': 'Dr. Provider',
        'video_appointments': video_appointments
    }
    return render(request, 'provider/video_consultation.html', context)
