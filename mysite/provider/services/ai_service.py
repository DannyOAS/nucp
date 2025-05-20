# provider/services/ai_scribe_service.py
import logging
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from provider.models import Provider, RecordingSession, ClinicalNote
from common.models import Appointment

logger = logging.getLogger(__name__)

class AIScribeService:
    """Service layer for AI transcription and clinical note generation."""
    
    @staticmethod
    def get_dashboard_data(provider_id):
        """
        Get AI scribe dashboard data:
        - Recordings
        - Notes
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get recent recordings
            recordings = RecordingSession.objects.filter(
                provider=provider
            ).order_by('-start_time')[:20]  # Limit to 20 most recent
            
            # Get recent clinical notes
            notes = ClinicalNote.objects.filter(
                provider=provider
            ).order_by('-created_at')[:20]  # Limit to 20 most recent
            
            return {
                'recordings': recordings,
                'notes': notes
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'recordings': [],
                'notes': []
            }
        except Exception as e:
            logger.error(f"Error in get_dashboard_data: {str(e)}")
            raise
    
    @staticmethod
    def get_recent_scribe_data(provider_id):
        """
        Get recent AI scribe data for dashboard
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get most recent recordings
            recent_recordings = RecordingSession.objects.filter(
                provider=provider
            ).order_by('-start_time')[:5]  # Limit to 5 most recent
            
            # Check if AI Scribe is enabled
            is_enabled = True
            
            # Try to check AI configuration if available
            try:
                from provider.models import AIModelConfig
                is_enabled = AIModelConfig.objects.filter(
                    model_type__in=['transcription', 'clinical_note'],
                    is_active=True
                ).exists()
            except (ImportError, AttributeError):
                pass
            
            return {
                'enabled': is_enabled,
                'recent_recordings': recent_recordings
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'enabled': False,
                'recent_recordings': []
            }
        except Exception as e:
            logger.error(f"Error in get_recent_scribe_data: {str(e)}")
            return {
                'enabled': False,
                'recent_recordings': []
            }
    
    @staticmethod
    def start_recording(provider_id, appointment_id):
        """
        Start a recording session
        """
        # Use VideoService for consistency
        from provider.services.video_service import VideoService
        return VideoService.start_recording(appointment_id, provider_id)
    
    @staticmethod
    def stop_recording(provider_id, recording_id):
        """
        Stop a recording session
        """
        # Use VideoService for consistency
        from provider.services.video_service import VideoService
        return VideoService.stop_recording(recording_id, provider_id)
    
    @staticmethod
    def get_transcription(provider_id, recording_id):
        """
        Get transcription for a recording
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            recording = RecordingSession.objects.get(id=recording_id, provider=provider)
            
            # Build recording data object
            recording_data = {
                'id': recording.id,
                'jitsi_recording_id': recording.jitsi_recording_id,
                'start_time': recording.start_time,
                'end_time': recording.end_time,
                'transcription_status': recording.transcription_status,
                'transcription_text': recording.transcription_text
            }
            
            # Get appointment details if available
            if recording.appointment:
                recording_data['appointment'] = {
                    'id': recording.appointment.id,
                    'time': recording.appointment.time,
                    'patient_name': (f"{recording.appointment.patient.first_name} {recording.appointment.patient.last_name}" 
                                    if recording.appointment.patient else "Unknown Patient")
                }
            
            # Calculate duration if available
            if recording.start_time and recording.end_time:
                duration_seconds = (recording.end_time - recording.start_time).total_seconds()
                recording_data['duration_minutes'] = round(duration_seconds / 60)
            
            return {
                'success': True,
                'recording': recording,
                'recording_data': recording_data
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except RecordingSession.DoesNotExist:
            logger.error(f"Recording with ID {recording_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Recording session not found'
            }
        except Exception as e:
            logger.error(f"Error getting transcription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_note(provider_id, recording_id):
        """
        Generate a clinical note from recording
        """
        # Use VideoService for consistency
        from provider.services.video_service import VideoService
        return VideoService.generate_clinical_note(recording_id, provider_id)
    
    @staticmethod
    def get_clinical_note(provider_id, note_id):
        """
        Get clinical note details
        """
        # Use VideoService for consistency
        from provider.services.video_service import VideoService
        return VideoService.get_clinical_note(note_id, provider_id)
    
    @staticmethod
    def update_clinical_note(provider_id, note_id, update_data, user):
        """
        Update clinical note content
        """
        # Use VideoService for consistency
        from provider.services.video_service import VideoService
        return VideoService.update_clinical_note(note_id, provider_id, update_data, user)
