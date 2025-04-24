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


class AppointmentService:
    """Service layer for appointment-related operations."""
    
    @staticmethod
    def get_appointments_dashboard(patient_id):
        """Get all appointment data needed for appointments dashboard."""
        upcoming_appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
        past_appointments = AppointmentRepository.get_past_for_patient(patient_id)
        
        # Calculate counts
        upcoming_count = len(upcoming_appointments)
        past_count = len(past_appointments)
        provider_count = len(set([a.get('doctor', '') for a in upcoming_appointments + past_appointments]))
        
        return {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'upcoming_count': upcoming_count,
            'past_count': past_count,
            'provider_count': provider_count
        }
    
    @staticmethod
    def schedule_appointment(appointment_data):
        """Schedule a new appointment."""
        # In a real implementation, this would check for conflicts, etc.
        appointment = AppointmentRepository.create(appointment_data)
        
        # Would send confirmation email in real implementation
        # AppointmentService.send_confirmation_email(appointment)
        
        return appointment
    
    @staticmethod
    def reschedule_appointment(appointment_id, new_time_data):
        """Reschedule an existing appointment."""
        appointment = AppointmentRepository.get_by_id(appointment_id)
        
        if not appointment:
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        
        # Update appointment time
        updated_appointment = AppointmentRepository.update(
            appointment_id, 
            {'time': new_time_data.get('time')}
        )
        
        # Would send update email in real implementation
        # AppointmentService.send_update_email(updated_appointment)
        
        return {
            'success': True,
            'appointment': updated_appointment
        }

