# patient/services/video_service.py
from common.models import Appointment
from patient.models import Patient
from django.utils import timezone

class VideoService:
    """Service layer for patient video consultation operations"""
    
    @staticmethod
    def get_patient_video_dashboard(patient_id):
        """
        Get data for patient's video consultation dashboard
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing video appointments data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get upcoming video appointments
            upcoming_appointments = Appointment.objects.filter(
                patient=user,
                type='Virtual',
                status='Scheduled',
                time__gte=timezone.now()
            ).order_by('time')
            
            # Get past video appointments
            past_appointments = Appointment.objects.filter(
                patient=user,
                type='Virtual'
            ).exclude(
                status='Scheduled'
            ).order_by('-time')[:10]  # Limit to last 10
            
            return {
                'success': True,
                'upcoming_appointments': upcoming_appointments,
                'past_appointments': past_appointments
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'upcoming_appointments': [],
                'past_appointments': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'upcoming_appointments': [],
                'past_appointments': []
            }
    
    @staticmethod
    def join_video_appointment(appointment_id, patient_id):
        """
        Join a video appointment meeting
        
        Args:
            appointment_id: ID of the appointment
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result containing meeting URL if successful
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get appointment and verify ownership
            appointment = Appointment.objects.get(id=appointment_id, patient=user, type='Virtual')
            
            # Check if the appointment is scheduled and within the allowed time window
            appointment_time = appointment.time
            now = timezone.now()
            
            # Allow joining 15 minutes before and up to 30 minutes after the scheduled time
            time_window_start = appointment_time - timezone.timedelta(minutes=15)
            time_window_end = appointment_time + timezone.timedelta(minutes=30)
            
            if now < time_window_start:
                minutes_until = int((time_window_start - now).total_seconds() / 60)
                return {
                    'success': False,
                    'error': f"You can only join this appointment 15 minutes before the scheduled time. Please try again in {minutes_until} minutes."
                }
            
            if now > time_window_end:
                return {
                    'success': False,
                    'error': "This appointment has ended."
                }
            
            # Generate Jitsi meeting URL
            room_name = f"appointment-{appointment.id}"
            jitsi_url = f"https://meet.jit.si/{room_name}"
            
            return {
                'success': True,
                'appointment': appointment,
                'jitsi_url': jitsi_url
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Appointment.DoesNotExist:
            return {
                'success': False,
                'error': 'Appointment not found or not a video appointment'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
