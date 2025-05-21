# patient/services/appointment_service.py
from django.utils import timezone
from common.models import Appointment
from patient.models import Patient
from provider.models import Provider
from datetime import datetime, timedelta

class AppointmentService:
    """Service layer for patient appointment operations"""
    
    @staticmethod
    def get_patient_appointments(patient_id):
        """
        Get upcoming and past appointments for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing appointment data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get current date for filtering
            today = timezone.now()
            
            # Get upcoming appointments
            upcoming_appointments = Appointment.objects.filter(
                patient=user,
                time__gte=today
            ).order_by('time')
            
            # Get past appointments
            past_appointments = Appointment.objects.filter(
                patient=user,
                time__lt=today
            ).order_by('-time')[:10]  # Limit to last 10
            
            return {
                'success': True,
                'upcoming_appointments': upcoming_appointments,
                'past_appointments': past_appointments,
                'today': today
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'upcoming_appointments': [],
                'past_appointments': [],
                'today': timezone.now()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'upcoming_appointments': [],
                'past_appointments': [],
                'today': timezone.now()
            }
    
    @staticmethod
    def get_scheduling_form_data(patient_id):
        """
        Get data needed for appointment scheduling form
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Form data including available providers, dates and times
        """
        try:
            # Get available providers
            available_providers = Provider.objects.filter(is_active=True)
            
            # Generate available dates (next two weeks)
            available_dates = []
            start_date = timezone.now().date()
            for i in range(14):  # Next two weeks
                available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
            
            # Standard appointment times
            available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
            
            return {
                'success': True,
                'available_providers': available_providers,
                'available_dates': available_dates,
                'available_times': available_times
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'available_providers': [],
                'available_dates': [],
                'available_times': []
            }
    
    @staticmethod
    def schedule_appointment(patient_id, form_data):
        """
        Schedule a new appointment
        
        Args:
            patient_id: ID of the patient
            form_data: Form data containing appointment details
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Extract form data
            doctor_id = form_data.get('doctor')
            appointment_date = form_data.get('appointment_date')
            appointment_time = form_data.get('appointment_time')
            appointment_type = form_data.get('appointment_type')
            reason = form_data.get('reason')
            notes = form_data.get('notes', '')
            
            # Validate required fields
            if not all([doctor_id, appointment_date, appointment_time, appointment_type, reason]):
                return {
                    'success': False,
                    'error': 'All required fields must be provided'
                }
            
            # Parse datetime
            datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')
                appointment_datetime = timezone.make_aware(appointment_datetime)
            except ValueError:
                return {
                    'success': False,
                    'error': 'Invalid date or time format'
                }
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=user,
                doctor_id=doctor_id,
                time=appointment_datetime,
                type=appointment_type,
                reason=reason,
                notes=notes,
                status='Scheduled'
            )
            
            return {
                'success': True,
                'appointment': appointment
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_appointment_for_reschedule(appointment_id, patient_id):
        """
        Get appointment data for rescheduling
        
        Args:
            appointment_id: ID of the appointment to reschedule
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result containing appointment data if successful
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get appointment and verify ownership
            appointment = Appointment.objects.get(id=appointment_id, patient=user)
            
            return {
                'success': True,
                'appointment': appointment
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Appointment.DoesNotExist:
            return {
                'success': False,
                'error': 'Appointment not found or not authorized'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def reschedule_appointment(appointment_id, patient_id, form_data):
        """
        Reschedule an existing appointment
        
        Args:
            appointment_id: ID of the appointment to reschedule
            patient_id: ID of the patient (for ownership verification)
            form_data: Form data containing new appointment details
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get appointment and verify ownership
            appointment = Appointment.objects.get(id=appointment_id, patient=user)
            
            # Extract form data
            appointment_date = form_data.get('appointment_date')
            appointment_time = form_data.get('appointment_time')
            
            # Validate required fields
            if not all([appointment_date, appointment_time]):
                return {
                    'success': False,
                    'error': 'Date and time must be provided'
                }
            
            # Parse new datetime
            datetime_str = f"{appointment_date} {appointment_time}"
            try:
                appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %I:%M %p')
                appointment_datetime = timezone.make_aware(appointment_datetime)
            except ValueError:
                return {
                    'success': False,
                    'error': 'Invalid date or time format'
                }
            
            # Update appointment
            appointment.time = appointment_datetime
            appointment.save()
            
            return {
                'success': True,
                'appointment': appointment
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Appointment.DoesNotExist:
            return {
                'success': False,
                'error': 'Appointment not found or not authorized'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def cancel_appointment(appointment_id, patient_id):
        """
        Cancel an appointment
        
        Args:
            appointment_id: ID of the appointment to cancel
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get appointment and verify ownership
            appointment = Appointment.objects.get(id=appointment_id, patient=user)
            
            # Cancel appointment
            appointment.status = 'Cancelled'
            appointment.save()
            
            return {
                'success': True
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Appointment.DoesNotExist:
            return {
                'success': False,
                'error': 'Appointment not found or not authorized'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
