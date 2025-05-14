# patient/views/video_views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
from common.models import Appointment
from patient.services.video_service import VideoService

# Uncomment for API-based implementation
# import requests
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def jitsi_video_view(request):
    """Jitsi video consultation view"""
    patient = request.patient
    
    # Get upcoming video appointments
    upcoming_video_appointments = Appointment.objects.filter(
        patient=request.user,
        type='Virtual',
        status='Scheduled'
    ).order_by('time')
    
    # Get past video appointments
    past_video_appointments = Appointment.objects.filter(
        patient=request.user,
        type='Virtual'
    ).exclude(
        status='Scheduled'
    ).order_by('-time')[:10]
    
    context = {
       'patient': patient,
       'patient_name': patient.full_name,
       'upcoming_appointments': upcoming_video_appointments,
       'past_appointments': past_video_appointments,
       'active_section': 'video'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get upcoming video appointments
    #     upcoming_response = requests.get(
    #         f"{api_url}appointments/?type=Virtual&status=Scheduled",
    #         headers=headers
    #     )
    #     
    #     if upcoming_response.ok:
    #         upcoming_video_appointments = upcoming_response.json()['results']
    #     else:
    #         upcoming_video_appointments = []
    #     
    #     # Get past video appointments
    #     past_response = requests.get(
    #         f"{api_url}appointments/?type=Virtual&status=!Scheduled&limit=10",
    #         headers=headers
    #     )
    #     
    #     if past_response.ok:
    #         past_video_appointments = past_response.json()['results']
    #     else:
    #         past_video_appointments = []
    #     
    #     context = {
    #        'patient': patient,
    #        'patient_name': patient.full_name,
    #        'upcoming_appointments': upcoming_video_appointments,
    #        'past_appointments': past_video_appointments,
    #        'active_section': 'video'
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading video appointments: {str(e)}")
    
    return render(request, "patient/jitsi.html", context)

@patient_required
def join_video_appointment(request, appointment_id):
    """Join a video appointment"""
    patient = request.patient
    
    # Get the appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id, patient=request.user, type='Virtual')
        
        # Check if the appointment is scheduled and within the allowed time window
        from django.utils import timezone
        appointment_time = appointment.time
        now = timezone.now()
        
        # Allow joining 15 minutes before and up to 30 minutes after the scheduled time
        time_window_start = appointment_time - timezone.timedelta(minutes=15)
        time_window_end = appointment_time + timezone.timedelta(minutes=30)
        
        if not (time_window_start <= now <= time_window_end):
            messages.error(request, "You can only join this appointment 15 minutes before or 30 minutes after the scheduled time.")
            return redirect('patient:patient_jitsi')
        
        # Generate Jitsi meeting URL
        room_name = f"appointment-{appointment.id}"
        jitsi_url = f"https://meet.jit.si/{room_name}"
        
        context = {
            'patient': patient,
            'patient_name': patient.full_name,
            'appointment': appointment,
            'jitsi_url': jitsi_url,
            'active_section': 'video'
        }
        
        return render(request, "patient/jitsi_meeting.html", context)
        
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found or not a video appointment.")
        return redirect('patient:patient_jitsi')
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get appointment details
    #     appointment_response = requests.get(
    #         f"{api_url}appointments/{appointment_id}/",
    #         headers=headers
    #     )
    #     
    #     if not appointment_response.ok:
    #         messages.error(request, "Appointment not found or you don't have permission to view it.")
    #         return redirect('patient:patient_jitsi')
    #     
    #     appointment = appointment_response.json()
    #     
    #     # Check if it's a video appointment
    #     if appointment['type'] != 'Virtual':
    #         messages.error(request, "This is not a video appointment.")
    #         return redirect('patient:patient_jitsi')
    #     
    #     # Check time window
    #     # Parse appointment time
    #     from django.utils import timezone
    #     import datetime
    #     appointment_time = datetime.datetime.fromisoformat(appointment['time'].replace('Z', '+00:00'))
    #     now = timezone.now()
    #     
    #     # Allow joining 15 minutes before and up to 30 minutes after the scheduled time
    #     time_window_start = appointment_time - datetime.timedelta(minutes=15)
    #     time_window_end = appointment_time + datetime.timedelta(minutes=30)
    #     
    #     if not (time_window_start <= now <= time_window_end):
    #         messages.error(request, "You can only join this appointment 15 minutes before or 30 minutes after the scheduled time.")
    #         return redirect('patient:patient_jitsi')
    #     
    #     # Get meeting URL from API
    #     meeting_response = requests.get(
    #         f"{api_url}appointments/{appointment_id}/join/",
    #         headers=headers
    #     )
    #     
    #     if meeting_response.ok:
    #         meeting_data = meeting_response.json()
    #         jitsi_url = meeting_data.get('meeting_url')
    #         
    #         context = {
    #             'patient': patient,
    #             'patient_name': patient.full_name,
    #             'appointment': appointment,
    #             'jitsi_url': jitsi_url,
    #             'active_section': 'video'
    #         }
    #         
    #         return render(request, "patient/jitsi_meeting.html", context)
    #     else:
    #         messages.error(request, "Could not create video meeting.")
    #         return redirect('patient:patient_jitsi')
    # except Exception as e:
    #     messages.error(request, f"Error joining video appointment: {str(e)}")
    #     return redirect('patient:patient_jitsi')
