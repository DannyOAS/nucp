# provider/services/video_service.py
import logging
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import uuid

from provider.models import Provider, RecordingSession, ClinicalNote
from common.models import Appointment

logger = logging.getLogger(__name__)

class VideoService:
    """Service layer for video consultation and recording operations."""
    
    @staticmethod
    def get_provider_video_dashboard(provider_id):
        """
        Get video dashboard data:
        - Video appointments
        - Active sessions
        - Recent recordings
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            now = timezone.now()
            
            # Get upcoming video appointments
            video_appointments = Appointment.objects.filter(
                doctor=provider,
                type='Virtual',
                time__gte=now,
                status='Scheduled'
            ).order_by('time')
            
            # Get active recording sessions
            active_sessions = RecordingSession.objects.filter(
                provider=provider,
                end_time__isnull=True  # Sessions that haven't ended yet
            ).order_by('start_time')
            
            # Get recent recordings
            recent_recordings = RecordingSession.objects.filter(
                provider=provider,
                end_time__isnull=False  # Completed recordings
            ).order_by('-end_time')[:10]  # Last 10 recordings
            
            return {
                'video_appointments': video_appointments,
                'active_sessions': active_sessions,
                'recent_recordings': recent_recordings
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'video_appointments': [],
                'active_sessions': [],
                'recent_recordings': []
            }
        except Exception as e:
            logger.error(f"Error in get_provider_video_dashboard: {str(e)}")
            raise
    
    @staticmethod
    def start_recording(appointment_id, provider_id):
        """
        Start a new recording session
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            appointment = Appointment.objects.get(id=appointment_id, doctor=provider, type='Virtual')
            
# provider/services/video_service.py (continued)
            # Check if there's already an active recording for this appointment
            existing_recording = RecordingSession.objects.filter(
                appointment=appointment,
                provider=provider,
                end_time__isnull=True
            ).first()
            
            if existing_recording:
                return {
                    'success': False,
                    'error': 'A recording session is already in progress for this appointment'
                }
            
            # Generate a unique recording ID
            jitsi_recording_id = f"rec-{uuid.uuid4()}"
            
            # Create the recording session
            recording = RecordingSession.objects.create(
                appointment=appointment,
                provider=provider,
                jitsi_recording_id=jitsi_recording_id,
                start_time=timezone.now(),
                transcription_status='pending'
            )
            
            # Try to start the actual recording via API if available
            recording_api_result = {'success': True}
            try:
                # This would call the video platform's API to start recording
                # Implementation depends on the video platform being used (Jitsi, Zoom, etc.)
                # For now, we'll assume success
                pass
            except Exception as e:
                recording_api_result = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Error starting recording via API: {str(e)}")
            
            return {
                'success': True,
                'recording_id': recording.id,
                'jitsi_recording_id': jitsi_recording_id,
                'api_result': recording_api_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Appointment.DoesNotExist:
            logger.error(f"Appointment with ID {appointment_id} not found, not a virtual appointment, or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Appointment not found or not a virtual appointment'
            }
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def stop_recording(recording_id, provider_id):
        """
        Stop an active recording session
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            recording = RecordingSession.objects.get(id=recording_id, provider=provider, end_time__isnull=True)
            
            # Mark the recording as ended
            recording.end_time = timezone.now()
            recording.save()
            
            # Try to stop the actual recording via API if available
            recording_api_result = {'success': True}
            try:
                # This would call the video platform's API to stop recording
                # Implementation depends on the video platform being used (Jitsi, Zoom, etc.)
                # For now, we'll assume success
                pass
            except Exception as e:
                recording_api_result = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Error stopping recording via API: {str(e)}")
            
            # Start transcription process
            transcription_result = {'success': True}
            try:
                # This would initiate the transcription process, possibly via a background task
                # For now, we'll update the status and assume success
                recording.transcription_status = 'processing'
                recording.save()
                
                # In a real implementation, you might start a background task:
                # from tasks import transcribe_recording
                # transcribe_recording.delay(recording_id)
            except Exception as e:
                transcription_result = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Error initiating transcription: {str(e)}")
            
            return {
                'success': True,
                'recording_id': recording.id,
                'transcription_status': recording.transcription_status,
                'api_result': recording_api_result,
                'transcription_result': transcription_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except RecordingSession.DoesNotExist:
            logger.error(f"Recording with ID {recording_id} not found, already ended, or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Recording session not found or already ended'
            }
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_recording_details(recording_id, provider_id):
        """
        Get detailed info for a recording
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            recording = RecordingSession.objects.get(id=recording_id, provider=provider)
            
            # Get associated notes if any
            notes = ClinicalNote.objects.filter(transcription=recording)
            
            # Get appointment details
            appointment_data = None
            if recording.appointment:
                appointment_data = {
                    'id': recording.appointment.id,
                    'time': recording.appointment.time,
                    'patient': None
                }
                
                # Get patient details if available
                if recording.appointment.patient:
                    patient_name = f"{recording.appointment.patient.first_name} {recording.appointment.patient.last_name}"
                    appointment_data['patient'] = {
                        'id': recording.appointment.patient.id,
                        'name': patient_name
                    }
            
            # Calculate duration if available
            duration_minutes = None
            if recording.start_time and recording.end_time:
                duration_seconds = (recording.end_time - recording.start_time).total_seconds()
                duration_minutes = round(duration_seconds / 60)
            
            # Build recording data object
            recording_data = {
                'id': recording.id,
                'jitsi_recording_id': recording.jitsi_recording_id,
                'start_time': recording.start_time,
                'end_time': recording.end_time,
                'duration_minutes': duration_minutes,
                'transcription_status': recording.transcription_status,
                'transcription_text': recording.transcription_text,
                'appointment': appointment_data
            }
            
            return {
                'success': True,
                'recording': recording,
                'recording_data': recording_data,
                'notes': notes
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
            logger.error(f"Error getting recording details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_clinical_note(recording_id, provider_id):
        """
        Generate a clinical note from a recording
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            recording = RecordingSession.objects.get(id=recording_id, provider=provider)
            
            # Check if transcription is complete
            if recording.transcription_status != 'completed':
                return {
                    'success': False,
                    'error': 'Transcription is not yet complete. Current status: ' + recording.transcription_status
                }
            
            # Check if transcription text is available
            if not recording.transcription_text:
                return {
                    'success': False,
                    'error': 'Transcription text is empty'
                }
            
            # Check if a note already exists
            existing_note = ClinicalNote.objects.filter(
                transcription=recording,
                provider=provider
            ).first()
            
            if existing_note:
                return {
                    'success': False,
                    'error': 'A clinical note already exists for this recording',
                    'note_id': existing_note.id
                }
            
            # Generate AI-assisted clinical note if AI service is available
            ai_generated_text = None
            ai_result = {'success': True}
            try:
                # In a real implementation, this would call an AI service
                # For now, we'll create a simple summary
                from provider.services.ai_service import AIService
                ai_result = AIService.generate_clinical_note(recording.transcription_text)
                
                if ai_result.get('success'):
                    ai_generated_text = ai_result.get('generated_text')
                else:
                    logger.warning(f"AI note generation failed: {ai_result.get('error')}")
                    # Create a simple placeholder
                    ai_generated_text = "Generated note based on transcription."
            except (ImportError, AttributeError):
                # If AI service is not available, create a basic template
                ai_generated_text = "Please review transcription and complete clinical note."
                ai_result = {
                    'success': False,
                    'error': 'AI service not available'
                }
            
            # Create the clinical note
            note = ClinicalNote.objects.create(
                appointment=recording.appointment,
                provider=provider,
                transcription=recording,
                ai_generated_text=ai_generated_text,
                provider_edited_text='',  # Empty until provider edits
                status='draft',
                created_by=provider.user
            )
            
            return {
                'success': True,
                'note_id': note.id,
                'ai_result': ai_result
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
            logger.error(f"Error generating clinical note: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_clinical_note(note_id, provider_id):
        """
        Get detailed info for a clinical note
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            note = ClinicalNote.objects.get(id=note_id, provider=provider)
            
            # Get appointment details
            appointment_data = None
            if note.appointment:
                appointment_data = {
                    'id': note.appointment.id,
                    'time': note.appointment.time,
                    'patient': None
                }
                
                # Get patient details if available
                if note.appointment.patient:
                    patient_name = f"{note.appointment.patient.first_name} {note.appointment.patient.last_name}"
                    appointment_data['patient'] = {
                        'id': note.appointment.patient.id,
                        'name': patient_name
                    }
            
            # Build note data object
            note_data = {
                'id': note.id,
                'appointment_id': note.appointment.id if note.appointment else None,
                'transcription_id': note.transcription.id if note.transcription else None,
                'ai_generated_text': note.ai_generated_text,
                'provider_edited_text': note.provider_edited_text,
                'status': note.status,
                'created_at': note.created_at,
                'updated_at': note.updated_at,
                'appointment': appointment_data
            }
            
            return {
                'success': True,
                'note': note,
                'note_data': note_data
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except ClinicalNote.DoesNotExist:
            logger.error(f"Clinical note with ID {note_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Clinical note not found'
            }
        except Exception as e:
            logger.error(f"Error getting clinical note: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_clinical_note(note_id, provider_id, update_data, user):
        """
        Update a clinical note
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            note = ClinicalNote.objects.get(id=note_id, provider=provider)
            
            # Update the note fields
            if 'provider_edited_text' in update_data:
                note.provider_edited_text = update_data['provider_edited_text']
            
            if 'status' in update_data:
                # Validate status
                valid_statuses = ['draft', 'reviewed', 'finalized']
                if update_data['status'] in valid_statuses:
                    note.status = update_data['status']
            
            # Update last edited info
            note.last_edited_by = user
            
            # Save changes
            note.save()
            
            # If note is finalized and linked to appointment, update appointment status
            if note.status == 'finalized' and note.appointment:
                try:
                    note.appointment.status = 'Completed'
                    note.appointment.save()
                except Exception as e:
                    logger.warning(f"Error updating appointment status: {str(e)}")
            
            return {
                'success': True,
                'note_id': note.id,
                'status': note.status
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except ClinicalNote.DoesNotExist:
            logger.error(f"Clinical note with ID {note_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Clinical note not found'
            }
        except Exception as e:
            logger.error(f"Error updating clinical note: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
