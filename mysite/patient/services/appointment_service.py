# patient/services/appointment_service.py
from django.utils import timezone
from common.models import Appointment
from patient.models import Patient
from provider.models import Provider
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
class AppointmentService:
    """OPTIMIZED: Service with efficient appointment queries"""
    
    @staticmethod
    def get_patient_appointments(patient_id):
        """
        OPTIMIZED: Get appointments with all related data in minimal queries
        """
        try:
            # OPTIMIZED: Load patient with user in single query
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            from django.utils import timezone
            today = timezone.now()
            
            # OPTIMIZED: Load upcoming appointments with all related data
            upcoming_appointments = Appointment.objects.filter(
                patient=user,
                time__gte=today
            ).select_related(
                'doctor',                # Join Provider
                'doctor__user',          # Join Provider's User
                'patient'                # Join Patient's User (already have, but explicit)
            ).order_by('time')
            
            # OPTIMIZED: Load past appointments with related data
            past_appointments = Appointment.objects.filter(
                patient=user,
                time__lt=today
            ).select_related(
                'doctor',
                'doctor__user',
                'patient'
            ).order_by('-time')[:10]  # Limit early for performance
            
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

    @staticmethod
    def get_patient_healthcare_providers(patient_id):
        """
        OPTIMIZED: Get healthcare providers with single efficient query
        """
        try:
            # OPTIMIZED: Load patient with primary provider in single query
            patient = Patient.objects.select_related(
                'user',
                'primary_provider',
                'primary_provider__user'
            ).get(id=patient_id)
            
            user = patient.user
            
            # OPTIMIZED: Single query to get all providers from appointments with user data
            provider_data = Appointment.objects.filter(
                patient=user
            ).select_related(
                'doctor',
                'doctor__user'
            ).values(
                'doctor__id',
                'doctor__user__first_name',
                'doctor__user__last_name', 
                'doctor__specialty'
            ).distinct()
            
            providers = []
            seen_ids = set()
            
            # Process appointment providers (no additional queries needed)
            for data in provider_data:
                if data['doctor__id'] and data['doctor__id'] not in seen_ids:
                    providers.append({
                        'id': data['doctor__id'],
                        'name': f"{data['doctor__user__first_name']} {data['doctor__user__last_name']}".strip(),
                        'specialty': data['doctor__specialty'] or 'General Practice',
                        'clinic': 'Northern Health Clinic'
                    })
                    seen_ids.add(data['doctor__id'])
            
            # Add primary provider if not already included (already loaded with select_related)
            if patient.primary_provider and patient.primary_provider.id not in seen_ids:
                providers.append({
                    'id': patient.primary_provider.id,
                    'name': f"{patient.primary_provider.user.first_name} {patient.primary_provider.user.last_name}".strip(),
                    'specialty': patient.primary_provider.specialty or 'General Practice',
                    'clinic': 'Northern Health Clinic'
                })
            
            return {
                'success': True,
                'healthcare_providers': providers
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'healthcare_providers': []
            }

    @staticmethod
    def get_scheduling_form_data(patient_id):
        """
        OPTIMIZED: Get data needed for appointment scheduling form
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Form data including available providers, dates and times
        """
        try:
            # OPTIMIZED: Get available providers with single query
            available_providers = Provider.objects.filter(
                is_active=True
            ).select_related('user').order_by('user__last_name')
            
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
            logger.error(f"Error in get_scheduling_form_data: {str(e)}")
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
        OPTIMIZED: Schedule a new appointment
        
        Args:
            patient_id: ID of the patient
            form_data: Form data containing appointment details
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
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
            
            # OPTIMIZED: Get provider with single query
            try:
                provider = Provider.objects.select_related('user').get(id=doctor_id)
            except Provider.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Provider not found'
                }
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=user,
                doctor=provider,
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
            logger.error(f"Error in schedule_appointment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_appointment_for_reschedule(appointment_id, patient_id):
        """
        OPTIMIZED: Get appointment data for rescheduling
        
        Args:
            appointment_id: ID of the appointment to reschedule
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result containing appointment data if successful
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Get appointment with provider info in single query
            appointment = Appointment.objects.select_related(
                'doctor',
                'doctor__user'
            ).get(id=appointment_id, patient=user)
            
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
            logger.error(f"Error in get_appointment_for_reschedule: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def reschedule_appointment(appointment_id, patient_id, form_data):
        """
        OPTIMIZED: Reschedule an existing appointment
        
        Args:
            appointment_id: ID of the appointment to reschedule
            patient_id: ID of the patient (for ownership verification)
            form_data: Form data containing new appointment details
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Get appointment with single query
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
            logger.error(f"Error in reschedule_appointment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def cancel_appointment(appointment_id, patient_id):
        """
        OPTIMIZED: Cancel an appointment
        
        Args:
            appointment_id: ID of the appointment to cancel
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Get appointment with single query
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
            logger.error(f"Error in cancel_appointment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
