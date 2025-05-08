# services/enhanced_appointment_service.py
from datetime import datetime, timedelta
import logging
import json
import uuid
import pytz
from django.conf import settings
from django.core.mail import send_mail

from .calendar_service import CalendarService
from theme_name.repositories import (
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
        # Get CalDAV settings from Django settings
        caldav_url = getattr(settings, 'CALDAV_URL', 'https://mail.yourserver.com/SOGo/dav/')
        
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
            
            provider_caldav_url = f"{caldav_url}{username}/"
            logger.debug(f"Creating calendar service for provider {provider_id} at {provider_caldav_url}")
            return CalendarService(provider_caldav_url, username, password)
        else:
            # Fall back to system calendar
            system_username = getattr(settings, 'CALDAV_SYSTEM_USERNAME', 'system@example.com')
            system_password = getattr(settings, 'CALDAV_SYSTEM_PASSWORD', 'password')
            logger.debug(f"Creating system calendar service with {system_username}")
            return CalendarService(caldav_url, system_username, system_password)
    
    @staticmethod
    def _appointment_to_calendar_event(appointment, patient_data=None):
        """Convert appointment data to calendar event data."""
        # Get patient information
        if not patient_data and appointment.get('patient_id'):
            patient_data = PatientRepository.get_by_id(appointment.get('patient_id'))
        
        # Parse appointment time string to datetime
        # Example format: "Apr 3, 2025 - 10:00 AM"
        appointment_time = appointment.get('time')
        start_time = None
        
        try:
            if isinstance(appointment_time, str):
                # Try to parse the string time format
                if '-' in appointment_time:
                    date_part, time_part = appointment_time.split('-', 1)
                    datetime_str = f"{date_part.strip()} {time_part.strip()}"
                    # Try different date formats
                    for fmt in ['%b %d, %Y %I:%M %p', '%B %d, %Y %I:%M %p']:
                        try:
                            start_time = datetime.strptime(datetime_str, fmt)
                            break
                        except ValueError:
                            continue
                else:
                    # Try direct parsing if no hyphen
                    try:
                        start_time = datetime.strptime(appointment_time, '%b %d, %Y %I:%M %p')
                    except ValueError:
                        start_time = datetime.strptime(appointment_time, '%B %d, %Y %I:%M %p')
            elif isinstance(appointment_time, datetime):
                # Already a datetime object
                start_time = appointment_time
                
            # If still not parsed, use a fallback
            if not start_time:
                raise ValueError(f"Could not parse appointment time: {appointment_time}")
                
            # Add timezone if needed
            if not start_time.tzinfo:
                tz = pytz.timezone(settings.TIME_ZONE) if hasattr(settings, 'TIME_ZONE') else pytz.UTC
                start_time = tz.localize(start_time)
                
        except Exception as e:
            logger.error(f"Error parsing appointment time: {appointment_time}, error: {e}")
            # Fallback to current time + 1 day if parsing fails
            start_time = datetime.now() + timedelta(days=1)
            
        # Default appointment duration: 30 minutes
        end_time = start_time + timedelta(minutes=30)
        
        # Create summary based on available data
        patient_name = "Patient"
        if patient_data:
            patient_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}".strip()
        elif appointment.get('patient_name'):
            patient_name = appointment.get('patient_name')
            
        summary = f"Appointment with {patient_name}"
            
        # Add appointment type to summary if available
        appointment_type = appointment.get('type', 'In-Person')
        if appointment_type:
            summary += f" ({appointment_type})"
            
        # Create a unique ID for the event
        uid = appointment.get('calendar_uid', f"appt-{uuid.uuid4()}")
        
        # Compose description with all relevant details
        description_parts = []
        if appointment.get('reason'):
            description_parts.append(f"Reason: {appointment.get('reason')}")
        if appointment.get('notes'):
            description_parts.append(f"Notes: {appointment.get('notes')}")
        
        # Add patient info if available
        if patient_data:
            description_parts.append(f"Patient: {patient_name}")
            if patient_data.get('primary_phone'):
                description_parts.append(f"Phone: {patient_data.get('primary_phone')}")
            if patient_data.get('email'):
                description_parts.append(f"Email: {patient_data.get('email')}")
            if patient_data.get('date_of_birth'):
                description_parts.append(f"DOB: {patient_data.get('date_of_birth')}")
        
        description = "\n".join(description_parts)
        
        # Determine location based on appointment type
        location = appointment.get('location', '')
        if not location:
            if appointment_type == 'Virtual':
                location = 'Virtual Meeting'
            else:
                location = 'Office'
        
        # Create attendees list
        attendees = []
        if patient_data and patient_data.get('email'):
            patient_email = patient_data.get('email')
            attendees.append(f"{patient_name} <{patient_email}>")
        
        return {
            'summary': summary,
            'start_time': start_time,
            'end_time': end_time,
            'description': description,
            'location': location,
            'uid': uid,
            'attendees': attendees
        }
    
    @staticmethod
    def _calendar_event_to_appointment(event, provider_id=None):
        """Convert calendar event data to appointment data."""
        summary = event.get('summary', '')
        start_time = event.get('start')
        end_time = event.get('end')
        uid = event.get('uid', '')
        description = event.get('description', '')
        location = event.get('location', '')
        
        # Format time for display
        formatted_time = start_time.strftime('%b %d, %Y - %I:%M %p')
        
        # Try to extract appointment type from summary
        appointment_type = "In-Person"  # Default
        if "Virtual" in summary or "Video" in summary:
            appointment_type = "Virtual"
            
        # Try to extract patient name from summary
        patient_name = "Unknown Patient"
        if "with" in summary:
            parts = summary.split("with", 1)
            if len(parts) > 1:
                patient_name = parts[1].split("(")[0].strip()
        
        # Extract reason for visit from description
        reason = ""
        notes = ""
        
        if description:
            lines = description.split('\n')
            for line in lines:
                if line.startswith("Reason:"):
                    reason = line.replace("Reason:", "").strip()
                elif line.startswith("Notes:"):
                    notes = line.replace("Notes:", "").strip()
        
        # Create appointment data structure
        appointment = {
            'id': hash(uid) % 10000,  # Generate a numerical ID from UID
            'patient_name': patient_name,
            'time': formatted_time,
            'type': appointment_type,
            'reason': reason,
            'location': location,
            'notes': notes,
            'doctor': f"Dr. {ProviderRepository.get_by_id(provider_id).get('last_name', 'Provider')}" if provider_id else "Doctor",
            'calendar_uid': uid,
            'status': 'Scheduled'
        }
        
        return appointment
    
    @staticmethod
    def get_appointments_dashboard(patient_id):
        """Get all appointment data needed for appointments dashboard with calendar integration."""
        # Get patient data to find associated provider
        patient = PatientRepository.get_by_id(patient_id)
        if not patient:
            logger.error(f"Patient {patient_id} not found")
            return {
                'upcoming_appointments': [],
                'past_appointments': [],
                'upcoming_count': 0,
                'past_count': 0,
                'provider_count': 0
            }
        
        # TODO: In a real implementation, get the actual provider assigned to this patient
        # For now, use a simple mapping for demo purposes
        provider_id = patient_id % 3 + 1
        
        # Try to get appointments from the calendar
        calendar_service = AppointmentService._get_calendar_service(provider_id)
        
        if calendar_service and calendar_service.ready:
            try:
                # Get events from calendar for next 90 days
                events = calendar_service.list_upcoming_events(days=90)
                
                # Filter events to find only those for this patient
                patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip().lower()
                
                upcoming_appointments = []
                past_appointments = []
                
                # Current time for comparison
                now = datetime.now()
                
                for event in events:
                    # Check if this event is for our patient
                    if 'summary' in event and patient_name in event['summary'].lower():
                        appointment = AppointmentService._calendar_event_to_appointment(event, provider_id)
                        
                        # Parse the appointment time for comparison
                        event_time = event.get('start')
                        
                        if event_time > now:
                            upcoming_appointments.append(appointment)
                        else:
                            # Mark as completed for past appointments
                            appointment['status'] = 'Completed'
                            past_appointments.append(appointment)
                
                # If no calendar appointments found, fall back to repository data
                if not upcoming_appointments and not past_appointments:
                    logger.info(f"No calendar appointments found for patient {patient_id}, checking repository")
                    upcoming_appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
                    past_appointments = AppointmentRepository.get_past_for_patient(patient_id)
                
                # Calculate counts
                upcoming_count = len(upcoming_appointments)
                past_count = len(past_appointments)
                
                # Get unique providers
                all_appointments = upcoming_appointments + past_appointments
                provider_count = len(set([a.get('doctor', '') for a in all_appointments]))
                
                return {
                    'upcoming_appointments': upcoming_appointments,
                    'past_appointments': past_appointments,
                    'upcoming_count': upcoming_count,
                    'past_count': past_count,
                    'provider_count': provider_count
                }
                
            except Exception as e:
                logger.error(f"Error fetching calendar appointments: {e}")
        
        # Fall back to repository data if calendar service failed or has no events
        logger.info(f"Using repository data for patient {patient_id} appointments")
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
        calendar_service = AppointmentService._get_calendar_service(provider_id)
        
        if calendar_service and calendar_service.ready:
            try:
                # Default to current date if not specified
                if not start_date:
                    start_date = datetime.now()
                    
                # Determine end date based on view type
                if not end_date:
                    if view_type == 'day':
                        end_date = start_date + timedelta(days=1)
                    elif view_type == 'week':
                        end_date = start_date + timedelta(days=7)
                    elif view_type == 'month':
                        # Approximate a month as 30 days
                        end_date = start_date + timedelta(days=30)
                    else:
                        end_date = start_date + timedelta(days=7)  # Default to week
                
                # Get events from calendar
                events = calendar_service.list_upcoming_events(days=(end_date - start_date).days)
                
                # Convert events to appointments
                appointments = []
                for event in events:
                    appointment = AppointmentService._calendar_event_to_appointment(event, provider_id)
                    appointments.append(appointment)
                
                # If no appointments found in calendar, fall back to repository
                if not appointments:
                    logger.info(f"No calendar appointments found for provider {provider_id}, checking repository")
                    appointments = ProviderRepository.get_appointments(provider_id)
                
                return appointments
                
            except Exception as e:
                logger.error(f"Error fetching provider calendar appointments: {e}")
        
        # Fall back to repository data if calendar service failed
        logger.info(f"Using repository data for provider {provider_id} appointments")
        return ProviderRepository.get_appointments(provider_id)
    
    @staticmethod
    def get_available_slots(provider_id, date, duration=30):
        """Get available appointment slots for a provider on a specific date."""
        calendar_service = AppointmentService._get_calendar_service(provider_id)
        
        if calendar_service and calendar_service.ready:
            try:
                # Get available time slots from calendar
                available_slots = calendar_service.get_available_slots(date, duration)
                
                # Format the slots for display
                formatted_slots = []
                for slot in available_slots:
                    formatted_slots.append({
                        'start_time': slot['start'],
                        'end_time': slot['end'],
                        'formatted_time': slot['start'].strftime('%I:%M %p')
                    })
                
                return formatted_slots
                
            except Exception as e:
                logger.error(f"Error getting available slots: {e}")
        
        # Fall back to default time slots if calendar service failed
        logger.info(f"Using default time slots for provider {provider_id}")
        
        # Default available hours: 9 AM to 5 PM
        default_slots = []
        start_hour = 9
        end_hour = 17
        
        slot_start = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
        
        while slot_start.hour < end_hour:
            slot_end = slot_start + timedelta(minutes=duration)
            
            default_slots.append({
                'start_time': slot_start,
                'end_time': slot_end,
                'formatted_time': slot_start.strftime('%I:%M %p')
            })
            
            slot_start += timedelta(minutes=duration)
        
        return default_slots
    
    @staticmethod
    def schedule_appointment(appointment_data, patient_id=None, provider_id=None):
        """Schedule a new appointment in both local system and calendar."""
        # Validate required data
        if not provider_id:
            logger.error("Provider ID required to schedule appointment")
            return None
            
        if not patient_id and not appointment_data.get('patient_id'):
            logger.error("Patient ID required to schedule appointment")
            return None
            
        # Get patient data
        patient_id = patient_id or appointment_data.get('patient_id')
        patient = PatientRepository.get_by_id(patient_id)
        
        if not patient:
            logger.error(f"Patient {patient_id} not found")
            return None
            
        # First save to our repository
        appointment = AppointmentRepository.create(appointment_data)
        
        # Then sync to calendar
        calendar_service = AppointmentService._get_calendar_service(provider_id)
        
        if calendar_service and calendar_service.ready:
            try:
                # Convert to calendar event format
                event_data = AppointmentService._appointment_to_calendar_event(appointment, patient)
                
                # Create event in calendar
                calendar_event_created = calendar_service.create_event(
                    summary=event_data['summary'],
                    start_time=event_data['start_time'],
                    end_time=event_data['end_time'],
                    description=event_data['description'],
                    uid=event_data['uid'],
                    attendees=event_data['attendees'],
                    location=event_data['location']
                )
                
                if calendar_event_created:
                    # Update appointment with calendar UID
                    appointment['calendar_uid'] = event_data['uid']
                    AppointmentRepository.update(appointment['id'], {'calendar_uid': event_data['uid']})
                    
                    # Send confirmation email to patient if email is available
                    if patient.get('email'):
                        try:
                            subject = "Appointment Confirmation"
                            message = f"""
Dear {patient.get('first_name', 'Patient')},

Your appointment has been scheduled.

Details:
- Provider: {appointment.get('doctor', 'Your healthcare provider')}
- Date and Time: {appointment.get('time', 'Scheduled time')}
- Type: {appointment.get('type', 'In-person')}
- Reason: {appointment.get('reason', 'Consultation')}
                            
If you need to reschedule or cancel, please contact us.

Thank you,
Northern Health Innovations
"""
                            # In a real implementation, send the email
                            # send_mail(
                            #     subject=subject,
                            #     message=message,
                            #     from_email=settings.DEFAULT_FROM_EMAIL,
                            #     recipient_list=[patient.get('email')],
                            #     fail_silently=True,
                            # )
                            logger.info(f"Appointment confirmation would be sent to {patient.get('email')}")
                        except Exception as e:
                            logger.error(f"Error sending confirmation email: {e}")
                else:
                    logger.warning(f"Failed to create calendar event for appointment {appointment['id']}")
            except Exception as e:
                logger.error(f"Error syncing appointment to calendar: {e}")
        
        return appointment
