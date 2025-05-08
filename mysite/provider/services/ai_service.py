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

class AIScribeService:
    """Service for AI transcription and clinical note generation"""
    
    @staticmethod
    def start_recording(appointment_id):
        """
        Start a recording session for an appointment
        
        Args:
            appointment_id: The ID of the appointment to record
            
        Returns:
            dict: Status of the recording session creation
        """
        try:
            # In a real implementation, would create a RecordingSession object
            # and connect to Jitsi API to start recording
            
            # Mock implementation
            recording_data = {
                'id': 1,  # Would be a real ID in actual implementation
                'appointment_id': appointment_id,
                'jitsi_recording_id': f"jitsi-{appointment_id}-{int(datetime.now().timestamp())}",
                'start_time': datetime.now().isoformat(),
                'status': 'recording'
            }
            
            logger.info(f"Started recording for appointment {appointment_id}")
            
            return {
                'success': True,
                'recording': recording_data
            }
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def stop_recording(recording_id):
        """
        Stop an active recording session
        
        Args:
            recording_id: The ID of the recording to stop
            
        Returns:
            dict: Status of the recording session stop
        """
        try:
            # In a real implementation, would update the RecordingSession
            # and call Jitsi API to stop recording
            
            # Mock implementation
            recording_data = {
                'id': recording_id,
                'end_time': datetime.now().isoformat(),
                'status': 'completed',
                'storage_path': f"/recordings/{recording_id}.mp4"
            }
            
            transcription_task = AIScribeService.process_transcription(recording_id)
            
            return {
                'success': True,
                'recording': recording_data,
                'transcription_status': 'initiated'
            }
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def process_transcription(recording_id):
        """
        Process a recording for transcription
        
        Args:
            recording_id: The ID of the recording to transcribe
            
        Returns:
            dict: Status of the transcription process
        """
        try:
            llm_response = AIScribeService._call_llm_api(
                endpoint="transcribe",
                payload={
                    "recording_id": recording_id,
                    "language": "en-US",
                    "format": "detailed"
                }
            )
            
            transcription_text = llm_response.get('transcription', 'No transcription available')
            
            return {
                'success': True,
                'recording_id': recording_id,
                'transcription_status': 'completed',
                'transcription_text': transcription_text[:100] + '...'
            }
        except Exception as e:
            logger.error(f"Error processing transcription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_clinical_notes(transcription_id):
        """
        Generate clinical notes from a transcription
        
        Args:
            transcription_id: The ID of the transcription
            
        Returns:
            dict: The generated clinical notes
        """
        try:
            transcription_text = (
                "Patient presents with complaints of headache and fatigue for the past week. "
                "No fever or other symptoms. Has history of migraines. Current medication includes..."
            )
            
            llm_response = AIScribeService._call_llm_api(
                endpoint="generate_notes",
                payload={
                    "transcription_text": transcription_text,
                    "format": "SOAP",
                    "include_diagnosis_codes": True
                }
            )
            
            clinical_note = llm_response.get('clinical_note', 'No clinical note generated')
            
            return {
                'success': True,
                'transcription_id': transcription_id,
                'clinical_note': clinical_note[:100] + '...'
            }
        except Exception as e:
            logger.error(f"Error generating clinical notes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _call_llm_api(endpoint, payload):
        """
        Helper method to call the LLM API
        
        Args:
            endpoint: The API endpoint to call
            payload: The payload to send
            
        Returns:
            dict: The API response
        """
        try:
            base_url = getattr(settings, 'LLM_API_URL', 'http://localhost:8000/api/')
            api_key = getattr(settings, 'LLM_API_KEY', 'mock-api-key')
            
            logger.info(f"Calling LLM API endpoint: {endpoint}")
            
            if endpoint == "transcribe":
                return {
                    "success": True,
                    "transcription": (
                        "Patient: I've been having these headaches for about a week now.\n"
                        "Doctor: Can you describe the pain?\n"
                        "Patient: It's a throbbing pain, mainly on the right side..."
                    ),
                    "confidence": 0.92,
                    "language_detected": "en-US",
                    "duration_seconds": 528
                }
            elif endpoint == "generate_notes":
                return {
                    "success": True,
                    "clinical_note": (
                        "SUBJECTIVE:\nPatient presents with complaints of headache and fatigue for the past week. "
                        "Describes the pain as throbbing, mainly on the right side of the head.\n\n"
                        "OBJECTIVE:\nVital signs stable. No fever. No neck stiffness or neurological deficits.\n\n"
                        "ASSESSMENT:\nMigraine headache, consistent with patient's history.\n\n"
                        "PLAN:\n1. Continue current medication.\n2. Increase water intake.\n3. Follow up in 2 weeks if symptoms persist."
                    ),
                    "diagnosis_codes": [
                        "G43.909: Migraine, unspecified, not intractable, without status migrainosus"
                    ],
                    "confidence": 0.88
                }
            else:
                return {
                    "success": False,
                    "error": "Unknown endpoint"
                }
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
