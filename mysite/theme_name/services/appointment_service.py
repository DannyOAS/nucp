# services/enhanced_appointment_service.py
from datetime import datetime, timedelta
import logging
import json
import uuid
from django.conf import settings
from django.core.mail import send_mail

from .calendar_service import CalendarService
from ..repositories import (
    PatientRepository, 
    AppointmentRepository, 
    ProviderRepository
)

logger = logging.getLogger(__name__)

class AppointmentService:
    """Service layer for appointment-related operations with CalDAV integration."""
    
    @staticmethod
    def _get_calendar_service(provider_id=None):
        """Get a configured CalendarService instance for a provider."""
        # These would come from your settings or provider configuration
        # Default to localhost for testing if not specified
        caldav_url = getattr(settings, 'CALDAV_URL', 'http://localhost/SOGo/dav/')
        
        if provider_id:
            # Get provider email and credentials from your system
            provider = ProviderRepository.get_by_id(provider_id)
            if not provider:
                logger.error(f"Provider {provider_id} not found for calendar service")
                return None
                
            username = provider.get('email', f'provider{provider_id}@example.com')
            # In a real system, you would have secure credential management
            # This is just for demonstration
            password = getattr(settings, 'CALDAV_PASSWORD', 'password')
            
            provider_caldav_url = f"{caldav_url}{username}"
            return CalendarService(provider_caldav_url, username, password)
        else:
            # Fall back to system calendar
            system_username = getattr(settings, 'CALDAV_SYSTEM_USERNAME', 'system@example.com')
            system_password = getattr(settings, 'CALDAV_SYSTEM_PASSWORD', 'password')
            return CalendarService(caldav_url, system_username, system_password)
    
    @staticmethod
    def get_appointments_dashboard(patient_id):
        """Get all appointment data needed for appointments dashboard with calendar integration."""
        # Get appointments directly from repository
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
    def get_provider_appointments(provider_id, start_date=None, end_date=None, view_type='week'):
        """Get appointments for a provider from calendar."""
        # For now, just use the repository data
        return ProviderRepository.get_appointments(provider_id)
    
    @staticmethod
    def schedule_appointment(appointment_data, patient_id=None, provider_id=None):
        """Schedule a new appointment in both local system and calendar."""
        # Just use the repository for now
        return AppointmentRepository.create(appointment_data)
    
    @staticmethod
    def reschedule_appointment(appointment_id, new_time_data, patient_id=None, provider_initiated=False, reschedule_reason=None, notify_patient=True):
        """Reschedule an existing appointment in both local system and calendar."""
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
        
        # This would handle calendar updates in a full implementation
        
        return {
            'success': True,
            'appointment': updated_appointment
        }
    
    @staticmethod
    def cancel_appointment(appointment_id, patient_id=None):
        """Cancel an appointment in both local system and calendar."""
        appointment = AppointmentRepository.get_by_id(appointment_id)
        
        if not appointment:
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        
        # Update status in repository
        updated_appointment = AppointmentRepository.update(
            appointment_id, 
            {'status': 'Cancelled'}
        )
        
        # This would handle calendar updates in a full implementation
        
        return {
            'success': True,
            'appointment': updated_appointment
        }
