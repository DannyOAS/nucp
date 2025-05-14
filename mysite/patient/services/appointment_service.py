# patient/services/appointment_service.py
from django.utils import timezone
from common.models import Appointment
from datetime import timedelta

class AppointmentService:
    @staticmethod
    def get_upcoming_appointments(patient):
        """Get upcoming appointments for a patient"""
        now = timezone.now()
        return Appointment.objects.filter(
            patient=patient.user,
            time__gte=now
        ).order_by('time')
    
    @staticmethod
    def get_past_appointments(patient, limit=10):
        """Get past appointments for a patient with optional limit"""
        now = timezone.now()
        return Appointment.objects.filter(
            patient=patient.user,
            time__lt=now
        ).order_by('-time')[:limit]
    
    @staticmethod
    def schedule_appointment(patient, doctor_id, appointment_date, appointment_time, 
                            appointment_type, reason, notes=''):
        """
        Schedule a new appointment
        
        Args:
            patient: Patient model instance
            doctor_id: ID of the provider
            appointment_date: Date string in YYYY-MM-DD format
            appointment_time: Time string in HH:MM AM/PM format
            appointment_type: Type of appointment (e.g., 'In-Person', 'Virtual')
            reason: Reason for the appointment
            notes: Additional notes (optional)
            
        Returns:
            Appointment: The created appointment object
            or
            dict: Error details if appointment couldn't be created
        """
        try:
            # Parse datetime
            from datetime import datetime
            datetime_str = f"{appointment_date} {appointment_time}"
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')
            appointment_datetime = timezone.make_aware(appointment_datetime)
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient.user,
                doctor_id=doctor_id,
                time=appointment_datetime,
                type=appointment_type,
                reason=reason,
                notes=notes,
                status='Scheduled'
            )
            
            return appointment
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def reschedule_appointment(appointment_id, patient, new_time_data):
        """
        Reschedule an existing appointment
        
        Args:
            appointment_id: ID of the appointment to reschedule
            patient: Patient model instance
            new_time_data: Dict with new time information
            
        Returns:
            dict: Success or error information
        """
        try:
            # Get appointment and verify ownership
            appointment = Appointment.objects.get(id=appointment_id, patient=patient.user)
            
            # Parse new datetime
            from datetime import datetime
            datetime_str = new_time_data.get('time')
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d - %I:%M %p')
            appointment_datetime = timezone.make_aware(appointment_datetime)
            
            # Update appointment
            appointment.time = appointment_datetime
            appointment.save()
            
            return {'success': True, 'appointment': appointment}
            
        except Appointment.DoesNotExist:
            return {'success': False, 'error': 'Appointment not found or not authorized'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def cancel_appointment(appointment_id, patient):
        """
        Cancel an appointment
        
        Args:
            appointment_id: ID of the appointment to cancel
            patient: Patient model instance
            
        Returns:
            dict: Success or error information
        """
        try:
            # Get appointment and verify ownership
            appointment = Appointment.objects.get(id=appointment_id, patient=patient.user)
            
            # Cancel appointment
            appointment.status = 'Cancelled'
            appointment.save()
            
            return {'success': True}
            
        except Appointment.DoesNotExist:
            return {'success': False, 'error': 'Appointment not found or not authorized'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
