# patient/views/video.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.video_service import VideoService
from patient.utils import get_current_patient
from api.v1.patient.serializers import AppointmentSerializer

logger = logging.getLogger(__name__)

@patient_required
def jitsi_video_view(request):
    """
    Jitsi video consultation view showing upcoming virtual appointments.
    Uses service layer for data retrieval and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get video appointments data from service
        video_data = VideoService.get_patient_video_dashboard(patient.id)
        
        # Format appointments using API serializer if needed
        upcoming_appointments = video_data.get('upcoming_appointments', [])
        if hasattr(upcoming_appointments, 'model'):
            serializer = AppointmentSerializer(upcoming_appointments, many=True)
            video_data['upcoming_appointments'] = serializer.data
        
        past_appointments = video_data.get('past_appointments', [])
        if hasattr(past_appointments, 'model'):
            serializer = AppointmentSerializer(past_appointments, many=True)
            video_data['past_appointments'] = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'upcoming_appointments': video_data.get('upcoming_appointments', []),
            'past_appointments': video_data.get('past_appointments', []),
            'active_section': 'video'
        }
    except Exception as e:
        logger.error(f"Error retrieving video appointments: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'upcoming_appointments': [],
            'past_appointments': [],
            'active_section': 'video'
        }
        messages.error(request, "There was an error loading your video appointments.")
    
    return render(request, "patient/jitsi.html", context)

@patient_required
def join_video_appointment(request, appointment_id):
    """
    Join a video appointment meeting.
    Uses service layer for appointment verification and meeting URL generation.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Verify appointment and get meeting info from service
        meeting_data = VideoService.join_video_appointment(
            appointment_id=appointment_id,
            patient_id=patient.id
        )
        
        if not meeting_data.get('success', False):
            messages.error(request, meeting_data.get('error', "Error joining appointment."))
            return redirect('patient:patient_jitsi')
        
        # Format appointment data using serializer if needed
        appointment = meeting_data.get('appointment')
        if appointment and hasattr(appointment, '__dict__'):
            serializer = AppointmentSerializer(appointment)
            meeting_data['appointment'] = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'appointment': meeting_data.get('appointment'),
            'jitsi_url': meeting_data.get('jitsi_url'),
            'active_section': 'video'
        }
        
        return render(request, "patient/jitsi_meeting.html", context)
        
    except Exception as e:
        logger.error(f"Error joining video appointment: {str(e)}")
        messages.error(request, f"Error joining video appointment: {str(e)}")
        return redirect('patient:patient_jitsi')
