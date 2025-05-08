# services.py
import json
import os
from django.conf import settings
from datetime import datetime, timedelta
from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML
import requests
import logging
from django.core.mail import send_mail
from django.contrib import messages

from theme_name.repositories import (
    PatientRepository, 
    PrescriptionRepository, 
    AppointmentRepository, 
    MessageRepository, 
    ProviderRepository
)

logger = logging.getLogger(__name__)

# Import models
# In a real implementation, you would uncomment these imports
# from .models import RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument, AIModelConfig, AIUsageLog


#class JitsiService:
class VideoService:
    """Service layer for Jitsi video consultations."""
    
    @staticmethod
    def get_video_dashboard(patient_id):
        """Get all data needed for Jitsi video dashboard."""
        all_appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
        video_appointments = [a for a in all_appointments if a.get('type') == 'Virtual']
        
        return {
            'video_appointments': video_appointments,
            'upcoming_count': len(video_appointments)
        }
    
    @staticmethod
    def generate_meeting_link(appointment_id):
        """Generate a Jitsi meeting link for an appointment."""
        appointment = AppointmentRepository.get_by_id(appointment_id)
        
        if not appointment:
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        
        # In a real implementation, this would generate a secure meeting link
        meeting_id = f"northernhealth-{appointment_id}-{int(datetime.now().timestamp())}"
        meeting_link = f"https://meet.jit.si/{meeting_id}"
        
        # Update the appointment with the meeting link
        updated_appointment = AppointmentRepository.update(
            appointment_id, 
            {'meeting_link': meeting_link}
        )
        
        return {
            'success': True,
            'meeting_link': meeting_link,
            'appointment': updated_appointment
        }
