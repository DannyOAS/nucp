from django.shortcuts import render
from ...repositories import PatientRepository
from ...services import VideoService



def jitsi_video_view(request):
    """Jitsi video consultation view"""
    patient = PatientRepository.get_current(request)
    
    # Setup video consultation
    video_data = VideoService.get_video_dashboard(patient['id'])
    
    context = {
       'patient': patient,
       'patient_name': f"{patient['first_name']} {patient['last_name']}",
       'video_data': video_data,
       'active_section': 'video'
    }
    
    return render(request, "patient/jitsi.html", context)
