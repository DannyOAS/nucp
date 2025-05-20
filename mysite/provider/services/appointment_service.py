# provider/services/appointment_service.py
import logging
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta, date
import calendar

from provider.models import Provider
from patient.models import Patient
from common.models import Appointment

logger = logging.getLogger(__name__)

class AppointmentService:
    """Service layer for appointment-related operations."""
    
    @staticmethod
    def get_provider_calendar_view(provider_id, selected_date=None, view_type='week'):
        """
        Get calendar view data:
        - Appointments for selected time period
        - Today's appointments
        - Calendar data for rendering
        - Date navigation info
        - Stats
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            now = timezone.now()
            today = now.date()
            
            # Parse selected date if provided
            if selected_date:
                if isinstance(selected_date, str):
                    try:
                        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                    except ValueError:
                        selected_date = today
                elif isinstance(selected_date, datetime):
                    selected_date = selected_date.date()
            else:
                selected_date = today
            
            # Calculate date range based on view_type
            start_date = None
            end_date = None
            
            if view_type == 'day':
                start_date = selected_date
                end_date = selected_date
                date_display = selected_date.strftime('%A, %B %d, %Y')
                prev_date = (selected_date - timedelta(days=1)).strftime('%Y-%m-%d')
                next_date = (selected_date + timedelta(days=1)).strftime('%Y-%m-%d')
                
            elif view_type == 'week':
                # Start from Monday of the week containing selected_date
                weekday = selected_date.weekday()
                start_date = selected_date - timedelta(days=weekday)
                end_date = start_date + timedelta(days=6)  # End on Sunday
                date_display = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
                prev_date = (start_date - timedelta(days=7)).strftime('%Y-%m-%d')
                next_date = (start_date + timedelta(days=7)).strftime('%Y-%m-%d')
                
            elif view_type == 'month':
                # Start from 1st day of the month
                start_date = date(selected_date.year, selected_date.month, 1)
                # End on last day of the month
                last_day = calendar.monthrange(selected_date.year, selected_date.month)[1]
                end_date = date(selected_date.year, selected_date.month, last_day)
                date_display = selected_date.strftime('%B %Y')
                
                # Previous month
                if selected_date.month == 1:
                    prev_month = date(selected_date.year - 1, 12, 1)
                else:
                    prev_month = date(selected_date.year, selected_date.month - 1, 1)
                prev_date = prev_month.strftime('%Y-%m-%d')
                
                # Next month
                if selected_date.month == 12:
                    next_month = date(selected_date.year + 1, 1, 1)
                else:
                    next_month = date(selected_date.year, selected_date.month + 1, 1)
                next_date = next_month.strftime('%Y-%m-%d')
            
            # Get appointments for the selected date range
            appointments = Appointment.objects.filter(
                doctor=provider,
                time__date__gte=start_date,
                time__date__lte=end_date
            ).order_by('time')
            
            # Get today's appointments
            todays_appointments = Appointment.objects.filter(
                doctor=provider,
                time__date=today
            ).order_by('time')
            
            # Process appointments for calendar display
            calendar_data = AppointmentService.process_appointments_for_calendar(
                appointments, start_date, end_date, view_type
            )
            
            # Calculate stats
            stats = {
                'today_count': todays_appointments.count(),
                'upcoming_count': Appointment.objects.filter(
                    doctor=provider,
                    time__gt=now,
                    status='Scheduled'
                ).count(),
                'completed_count': Appointment.objects.filter(
                    doctor=provider,
                    status='Completed'
                ).count(),
                'cancelled_count': Appointment.objects.filter(
                    doctor=provider,
                    status='Cancelled'
                ).count()
            }
            
            return {
                'appointments': appointments,
                'todays_appointments': todays_appointments,
                'calendar_data': calendar_data,
                'selected_date': selected_date,
                'date_display': date_display,
                'prev_date': prev_date,
                'next_date': next_date,
                'stats': stats
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'appointments': [],
                'todays_appointments': [],
                'calendar_data': {},
                'selected_date': timezone.now().date(),
                'date_display': timezone.now().date().strftime('%B %d, %Y'),
                'prev_date': (timezone.now().date() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'next_date': (timezone.now().date() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'stats': {
                    'today_count': 0,
                    'upcoming_count': 0,
                    'completed_count': 0,
                    'cancelled_count': 0
                }
            }
        except Exception as e:
            logger.error(f"Error in get_provider_calendar_view: {str(e)}")
            raise
    
    @staticmethod
    def process_appointments_for_calendar(appointments, start_date, end_date, view_type):
        """
        Process appointments into format needed for calendar display
        Returns data structure based on view_type (day, week, month)
        """
        calendar_data = {}
        
        if view_type == 'day':
            # For day view, organize by hour
            hours = [(f"{h:02d}:00", []) for h in range(8, 20)]  # 8am to 8pm
            calendar_data = {
                'hours': hours,
                'date': start_date
            }
            
            # Add appointments to appropriate hour slots
            for appointment in appointments:
# provider/services/appointment_service.py (continued)
                hour = appointment.time.hour
                if 8 <= hour < 20:  # Only handle hours in our display range
                    hour_slot = hours[hour - 8][1]  # Adjust index (8am is index 0)
                    hour_slot.append({
                        'id': appointment.id,
                        'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else "Unknown",
                        'time': appointment.time.strftime('%H:%M'),
                        'duration': getattr(appointment, 'duration', 30),  # Default 30 mins if not specified
                        'status': appointment.status,
                        'type': appointment.type,
                        'reason': appointment.reason,
                        'notes': appointment.notes
                    })
            
        elif view_type == 'week':
            # For week view, organize by day and hour
            weekdays = []
            current_date = start_date
            
            # Generate the week structure
            while current_date <= end_date:
                day_data = {
                    'date': current_date,
                    'name': current_date.strftime('%A'),
                    'formatted_date': current_date.strftime('%b %d'),
                    'appointments': []
                }
                weekdays.append(day_data)
                current_date += timedelta(days=1)
            
            # Add appointments to appropriate day
            for appointment in appointments:
                appointment_date = appointment.time.date()
                day_index = (appointment_date - start_date).days
                
                if 0 <= day_index < len(weekdays):
                    weekdays[day_index]['appointments'].append({
                        'id': appointment.id,
                        'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else "Unknown",
                        'time': appointment.time.strftime('%H:%M'),
                        'end_time': (appointment.time + timedelta(minutes=getattr(appointment, 'duration', 30))).strftime('%H:%M'),
                        'status': appointment.status,
                        'type': appointment.type,
                        'reason': appointment.reason,
                        'notes': appointment.notes
                    })
            
            calendar_data = {
                'weekdays': weekdays
            }
            
        elif view_type == 'month':
            # For month view, organize by day of month
            # First, get all dates in the month
            month_days = []
            current_date = start_date
            
            # Add leading days from previous month to start on Monday
            first_weekday = start_date.weekday()
            for i in range(first_weekday):
                previous_date = start_date - timedelta(days=first_weekday - i)
                month_days.append({
                    'date': previous_date,
                    'in_month': False,
                    'formatted_date': previous_date.strftime('%d'),
                    'appointments': []
                })
            
            # Add all days in the selected month
            while current_date <= end_date:
                month_days.append({
                    'date': current_date,
                    'in_month': True,
                    'formatted_date': current_date.strftime('%d'),
                    'is_today': current_date == timezone.now().date(),
                    'appointments': []
                })
                current_date += timedelta(days=1)
            
            # Add trailing days from next month to complete the grid
            last_weekday = end_date.weekday()
            for i in range(6 - last_weekday):
                next_date = end_date + timedelta(days=i + 1)
                month_days.append({
                    'date': next_date,
                    'in_month': False,
                    'formatted_date': next_date.strftime('%d'),
                    'appointments': []
                })
            
            # Add appointments to appropriate day
            for appointment in appointments:
                appointment_date = appointment.time.date()
                
                # Find matching day
                for day in month_days:
                    if day['date'] == appointment_date:
                        day['appointments'].append({
                            'id': appointment.id,
                            'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else "Unknown",
                            'time': appointment.time.strftime('%H:%M'),
                            'status': appointment.status,
                            'type': appointment.type
                        })
                        break
            
            # Group into weeks for the grid
            weeks = []
            for i in range(0, len(month_days), 7):
                weeks.append(month_days[i:i+7])
            
            calendar_data = {
                'weeks': weeks,
                'month_name': start_date.strftime('%B %Y')
            }
        
        return calendar_data
    
    @staticmethod
    def get_appointment_details(appointment_id, provider_id):
        """
        Get detailed info for a single appointment
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            appointment = Appointment.objects.get(id=appointment_id, doctor=provider)
            
            # Get patient details if available
            patient_data = None
            if appointment.patient:
                try:
                    patient = Patient.objects.get(user=appointment.patient)
                    patient_data = {
                        'id': patient.id,
                        'user_id': patient.user.id,
                        'first_name': patient.user.first_name,
                        'last_name': patient.user.last_name,
                        'full_name': f"{patient.user.first_name} {patient.user.last_name}",
                        'email': patient.user.email,
                        'date_of_birth': patient.date_of_birth,
                        'ohip_number': patient.ohip_number,
                        'primary_phone': patient.primary_phone
                    }
                except Patient.DoesNotExist:
                    # If patient record not found, use basic user info
                    patient_data = {
                        'user_id': appointment.patient.id,
                        'first_name': appointment.patient.first_name,
                        'last_name': appointment.patient.last_name,
                        'full_name': f"{appointment.patient.first_name} {appointment.patient.last_name}",
                        'email': appointment.patient.email
                    }
            
            return {
                'success': True,
                'appointment': appointment,
                'patient': patient_data
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Appointment.DoesNotExist:
            logger.error(f"Appointment with ID {appointment_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        except Exception as e:
            logger.error(f"Error in get_appointment_details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_appointment(provider_id, form_data):
        """
        Create a new appointment from form data
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get patient
            patient_id = form_data.get('patient_id')
            if not patient_id:
                return {
                    'success': False,
                    'error': 'Patient is required'
                }
            
            from django.contrib.auth.models import User
            try:
                patient = Patient.objects.get(id=patient_id)
                patient_user = patient.user
            except Patient.DoesNotExist:
                try:
                    # Try to get user directly
                    patient_user = User.objects.get(id=patient_id)
                except User.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Patient not found'
                    }
            
            # Parse appointment date and time
            appointment_date = form_data.get('appointment_date')
            appointment_time = form_data.get('appointment_time')
            
            if not appointment_date or not appointment_time:
                return {
                    'success': False,
                    'error': 'Appointment date and time are required'
                }
            
            try:
                # Parse date string
                if isinstance(appointment_date, str):
                    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                else:
                    date_obj = appointment_date
                
                # Parse time string
                if isinstance(appointment_time, str):
                    # Handle different time formats
                    try:
                        time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                    except ValueError:
                        try:
                            time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()
                        except ValueError:
                            return {
                                'success': False,
                                'error': 'Invalid time format'
                            }
                else:
                    time_obj = appointment_time
                
                # Combine date and time
                appointment_datetime = datetime.combine(date_obj, time_obj)
                
                # Convert to timezone-aware datetime if using timezone
                if settings.USE_TZ:
                    from django.utils import timezone
                    appointment_datetime = timezone.make_aware(appointment_datetime)
            except ValueError as e:
                return {
                    'success': False,
                    'error': f'Invalid date or time: {str(e)}'
                }
            
            # Get appointment type
            appointment_type = form_data.get('appointment_type', 'In-Person')
            if appointment_type not in ['In-Person', 'Virtual']:
                appointment_type = 'In-Person'  # Default to in-person
            
            # Create the appointment
            appointment = Appointment.objects.create(
                patient=patient_user,
                doctor=provider,
                time=appointment_datetime,
                type=appointment_type,
                reason=form_data.get('reason', ''),
                notes=form_data.get('notes', ''),
                status='Scheduled'
            )
            
            # Check if we need to sync with calendar
            calendar_sync_result = {'success': True}
            if hasattr(provider, 'calendar_sync_enabled') and provider.calendar_sync_enabled:
                try:
                    from common.services.calendar_service import CalendarService
                    calendar_sync_result = CalendarService.add_appointment_to_calendar(appointment)
                except (ImportError, AttributeError):
                    calendar_sync_result = {
                        'success': False,
                        'error': 'Calendar service not available'
                    }
            
            # Send notification if configured
            notification_result = {'success': True}
            try:
                from common.services.notification_service import NotificationService
                notification_result = NotificationService.send_appointment_notification(
                    appointment=appointment,
                    notification_type='created'
                )
            except (ImportError, AttributeError):
                notification_result = {
                    'success': False,
                    'error': 'Notification service not available'
                }
            
            return {
                'success': True,
                'appointment_id': appointment.id,
                'calendar_sync': calendar_sync_result,
                'notification': notification_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_scheduling_form_data(provider_id):
        """
        Get data needed for appointment scheduling form:
        - Patients list
        - Available dates/times
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get patients assigned to this provider
            patients = Patient.objects.filter(primary_provider=provider)
            
            # Generate available dates (next 30 days)
            available_dates = []
            start_date = timezone.now().date()
            for i in range(30):
                day_date = start_date + timedelta(days=i)
                # Skip weekends if needed
                if day_date.weekday() < 5:  # 0-4 is Monday-Friday
                    available_dates.append(day_date.strftime('%Y-%m-%d'))
            
            # Get provider's default working hours or use standard hours
            default_hours = getattr(provider, 'working_hours', {
                'start': '09:00',
                'end': '17:00',
                'lunch_start': '12:00',
                'lunch_end': '13:00'
            })
            
            # Generate available times
            available_times = []
            
            # Get appointment duration (default 30 minutes)
            duration = getattr(provider, 'default_appointment_duration', 30)
            
            # Parse working hours
            start_hour = 9  # Default 9 AM
            end_hour = 17   # Default 5 PM
            
            if 'start' in default_hours:
                try:
                    start_time = datetime.strptime(default_hours['start'], '%H:%M').time()
                    start_hour = start_time.hour
                except ValueError:
                    pass
            
            if 'end' in default_hours:
                try:
                    end_time = datetime.strptime(default_hours['end'], '%H:%M').time()
                    end_hour = end_time.hour
                except ValueError:
                    pass
            
            # Generate time slots
            current_hour = start_hour
            while current_hour < end_hour:
                # Skip lunch hour if defined
                is_lunch_hour = False
                if 'lunch_start' in default_hours and 'lunch_end' in default_hours:
                    try:
                        lunch_start = datetime.strptime(default_hours['lunch_start'], '%H:%M').time()
                        lunch_end = datetime.strptime(default_hours['lunch_end'], '%H:%M').time()
                        
                        current_time = time(current_hour, 0)
                        if lunch_start <= current_time < lunch_end:
                            is_lunch_hour = True
                    except ValueError:
                        pass
                
                if not is_lunch_hour:
                    # Format time with AM/PM
                    available_times.append(time(current_hour, 0).strftime('%-I:%M %p'))
                    
                    # Add additional slots based on duration
                    if duration < 60:
                        minutes = duration
                        while minutes < 60:
                            available_times.append(time(current_hour, minutes).strftime('%-I:%M %p'))
                            minutes += duration
                
                current_hour += 1
            
            return {
                'patients': patients,
                'available_dates': available_dates,
                'available_times': available_times
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'patients': [],
                'available_dates': [],
                'available_times': []
            }
        except Exception as e:
            logger.error(f"Error in get_scheduling_form_data: {str(e)}")
            return {
                'patients': [],
                'available_dates': [],
                'available_times': []
            }
    
    @staticmethod
    def reschedule_appointment(appointment_id, provider_id, form_data, provider_initiated=True):
        """
        Reschedule an existing appointment
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            appointment = Appointment.objects.get(id=appointment_id, doctor=provider)
            
            # Parse new appointment date and time
            appointment_date = form_data.get('appointment_date')
            appointment_time = form_data.get('appointment_time')
            
            if not appointment_date or not appointment_time:
                return {
                    'success': False,
                    'error': 'New appointment date and time are required'
                }
            
            try:
                # Parse date string
                if isinstance(appointment_date, str):
                    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                else:
                    date_obj = appointment_date
                
                # Parse time string
                if isinstance(appointment_time, str):
                    # Handle different time formats
                    try:
                        time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                    except ValueError:
                        try:
                            time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()
                        except ValueError:
                            return {
                                'success': False,
                                'error': 'Invalid time format'
                            }
                else:
                    time_obj = appointment_time
                
                # Combine date and time
                new_appointment_datetime = datetime.combine(date_obj, time_obj)
                
                # Convert to timezone-aware datetime if using timezone
                if settings.USE_TZ:
                    from django.utils import timezone
                    new_appointment_datetime = timezone.make_aware(new_appointment_datetime)
            except ValueError as e:
                return {
                    'success': False,
                    'error': f'Invalid date or time: {str(e)}'
                }
            
            # Store the old time for notification
            old_time = appointment.time
            
            # Update the appointment
            appointment.time = new_appointment_datetime
            appointment.save()
            
            # Check if we need to update calendar
            calendar_sync_result = {'success': True}
            if hasattr(provider, 'calendar_sync_enabled') and provider.calendar_sync_enabled:
                try:
                    from common.services.calendar_service import CalendarService
                    calendar_sync_result = CalendarService.update_appointment_in_calendar(appointment)
                except (ImportError, AttributeError):
                    calendar_sync_result = {
                        'success': False,
                        'error': 'Calendar service not available'
                    }
            
            # Send notification if configured
            notification_result = {'success': True}
            try:
                from common.services.notification_service import NotificationService
                notification_result = NotificationService.send_appointment_notification(
                    appointment=appointment,
                    notification_type='rescheduled',
                    additional_data={
                        'old_time': old_time,
                        'provider_initiated': provider_initiated
                    }
                )
            except (ImportError, AttributeError):
                notification_result = {
                    'success': False,
                    'error': 'Notification service not available'
                }
            
            return {
                'success': True,
                'appointment_id': appointment.id,
                'calendar_sync': calendar_sync_result,
                'notification': notification_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Appointment.DoesNotExist:
            logger.error(f"Appointment with ID {appointment_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_appointment_status(appointment_id, provider_id, status):
        """
        Update appointment status (Scheduled, Checked In, Completed, etc.)
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            appointment = Appointment.objects.get(id=appointment_id, doctor=provider)
            
            # Validate status
            valid_statuses = ['Scheduled', 'Checked In', 'In Progress', 'Completed', 'Cancelled', 'No Show']
            if status not in valid_statuses:
                return {
                    'success': False,
                    'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                }
            
            # Store old status for notification
            old_status = appointment.status
            
            # Update status
            appointment.status = status
            appointment.save()
            
            result = {
                'success': True,
                'appointment_id': appointment.id
            }
            
            # Special handling for cancelled appointments
            if status == 'Cancelled':
                # Check if we need to update calendar
                calendar_sync_result = {'success': True}
                if hasattr(provider, 'calendar_sync_enabled') and provider.calendar_sync_enabled:
                    try:
                        from common.services.calendar_service import CalendarService
                        calendar_sync_result = CalendarService.delete_appointment_from_calendar(appointment)
                    except (ImportError, AttributeError):
                        calendar_sync_result = {
                            'success': False,
                            'error': 'Calendar service not available'
                        }
                result['calendar_sync'] = calendar_sync_result
            
            # Send notification if configured
            notification_result = {'success': True}
            try:
                from common.services.notification_service import NotificationService
                notification_result = NotificationService.send_appointment_notification(
                    appointment=appointment,
                    notification_type='status_updated',
                    additional_data={
                        'old_status': old_status,
                        'new_status': status
                    }
                )
            except (ImportError, AttributeError):
                notification_result = {
                    'success': False,
                    'error': 'Notification service not available'
                }
            result['notification'] = notification_result
            
            return result
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Appointment.DoesNotExist:
            logger.error(f"Appointment with ID {appointment_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_appointment_for_reschedule(appointment_id, provider_id):
        """
        Get appointment data for rescheduling
        """
        # Call get_appointment_details for consistency
        return AppointmentService.get_appointment_details(appointment_id, provider_id)
