# services/calendarservice.py
from datetime import datetime, timedelta
import logging
import uuid
import pytz
import caldav
from icalendar import Calendar, Event, vText, vCalAddress
from django.conf import settings

logger = logging.getLogger(__name__)

class CalendarService:
    """Service to interact with a CalDAV calendar (SOGo)."""

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.client = None
        self.principal = None
        self.calendars = []
        self.ready = self._connect()
        
    def _connect(self):
        """Connect to the CalDAV server and get available calendars."""
        try:
            # Create a client connection
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password
            )
            
            # Get the principal
            self.principal = self.client.principal()
            
            # Get available calendars
            self.calendars = self.principal.calendars()
            
            # If no calendars found, create one
            if not self.calendars:
                logger.info(f"No calendars found for {self.username}, creating one")
                try:
                    # Try to create a default calendar
                    new_cal = self.principal.make_calendar(name="Appointments")
                    self.calendars = [new_cal]
                except Exception as e:
                    logger.error(f"Failed to create calendar: {e}")
                    return False
            
            logger.info(f"Successfully connected to CalDAV server for {self.username}")
            logger.info(f"Found {len(self.calendars)} calendars")
            return True
            
        except Exception as e:
            logger.error(f"CalDAV connection failed: {e}")
            return False
    
    def get_default_calendar(self):
        """Get the default calendar for this user."""
        if not self.ready or not self.calendars:
            return None
            
        # For simplicity, we'll use the first calendar as the default
        return self.calendars[0]
        
    def list_upcoming_events(self, days=7):
        """List events in the next `days` days."""
        try:
            if not self.ready:
                logger.warning("CalDAV server not ready, returning empty event list")
                return []
                
            # Get the default calendar
            calendar = self.get_default_calendar()
            if not calendar:
                logger.warning("No calendar available, returning empty event list")
                return []
                
            # Define the date range for the search
            now = datetime.now()
            future = now + timedelta(days=days)
            
            # Search for events in the date range
            events = calendar.date_search(start=now, end=future)
            
            # Convert the events to a more friendly format
            formatted_events = []
            for event in events:
                try:
                    # Parse the event data
                    vcal = Calendar.from_ical(event.data)
                    for component in vcal.walk('VEVENT'):
                        start = component.get('dtstart').dt
                        end = component.get('dtend').dt if component.get('dtend') else start + timedelta(minutes=30)
                        
                        # Convert datetime to Python datetime if needed
                        if hasattr(start, 'date'):
                            start_dt = start
                        else:  # All-day event
                            start_dt = datetime.combine(start, datetime.min.time())
                            
                        if hasattr(end, 'date'):
                            end_dt = end
                        else:  # All-day event
                            end_dt = datetime.combine(end, datetime.min.time())
                        
                        # Create a standardized event object
                        formatted_event = {
                            'uid': component.get('uid', str(uuid.uuid4())),
                            'summary': str(component.get('summary', 'No Title')),
                            'description': str(component.get('description', '')),
                            'location': str(component.get('location', '')),
                            'start': start_dt,
                            'end': end_dt,
                            'all_day': not hasattr(start, 'date'),
                            'url': event.url,
                            'data': event.data
                        }
                        
                        formatted_events.append(formatted_event)
                except Exception as e:
                    logger.error(f"Error parsing event: {e}")
                    # Add minimal information we can get from the event
                    formatted_events.append({
                        'uid': str(uuid.uuid4()),
                        'summary': 'Error parsing event',
                        'start': now,
                        'end': now + timedelta(minutes=30),
                        'url': event.url,
                        'data': event.data
                    })
            
            return formatted_events
                
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return []

    def create_event(self, summary, start_time, end_time, description=None, uid=None, attendees=None, location=None):
        """Create a new calendar event."""
        try:
            if not self.ready:
                logger.warning("CalDAV server not ready, skipping event creation")
                return False
                
            # Get the default calendar
            calendar = self.get_default_calendar()
            if not calendar:
                logger.warning("No calendar available, skipping event creation")
                return False
                
            # Create an iCalendar event
            cal = Calendar()
            event = Event()
            
            # Set the event properties
            event.add('summary', summary)
            event.add('dtstart', start_time)
            event.add('dtend', end_time)
            
            if description:
                event.add('description', description)
                
            if location:
                event.add('location', location)
                
            # Generate a UID if not provided
            if not uid:
                uid = f"django-{uuid.uuid4()}"
            event.add('uid', uid)
            
            # Add created and last modified timestamps
            now = datetime.now(pytz.utc)
            event.add('created', now)
            event.add('last-modified', now)
            
            # Add attendees if specified
            if attendees and isinstance(attendees, list):
                for attendee in attendees:
                    # Format: name <email>
                    attendee_parts = attendee.split('<')
                    if len(attendee_parts) > 1:
                        name = attendee_parts[0].strip()
                        email = attendee_parts[1].strip().rstrip('>')
                        
                        # Create a proper vCalAddress
                        attendee_prop = vCalAddress('mailto:' + email)
                        attendee_prop.params['cn'] = vText(name)
                        attendee_prop.params['ROLE'] = vText('REQ-PARTICIPANT')
                        event.add('attendee', attendee_prop)
            
            # Add the event to the calendar
            cal.add_component(event)
            calendar.save_event(cal.to_ical())
            
            logger.info(f"Created event: {summary} ({uid})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return False

    def delete_event(self, uid):
        """Delete an event by UID."""
        try:
            if not self.ready:
                logger.warning("CalDAV server not ready, skipping event deletion")
                return False
                
            # Get the default calendar
            calendar = self.get_default_calendar()
            if not calendar:
                logger.warning("No calendar available, skipping event deletion")
                return False
                
            # Find events with the specified UID
            events = calendar.search(uid=uid)
            
            if not events:
                logger.warning(f"No event found with UID: {uid}")
                return False
                
            # Delete the first matching event
            for event in events:
                event.delete()
                logger.info(f"Deleted event with UID: {uid}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False
    
    def update_event(self, uid, summary=None, start_time=None, end_time=None, description=None, location=None):
        """Update an existing event."""
        try:
            if not self.ready:
                logger.warning("CalDAV server not ready, skipping event update")
                return False
                
            # Get the default calendar
            calendar = self.get_default_calendar()
            if not calendar:
                logger.warning("No calendar available, skipping event update")
                return False
                
            # Find events with the specified UID
            events = calendar.search(uid=uid)
            
            if not events:
                logger.warning(f"No event found with UID: {uid}")
                return False
                
            # Update the first matching event
            for event in events:
                # Parse the event data
                vcal = Calendar.from_ical(event.data)
                
                for component in vcal.walk('VEVENT'):
                    # Update the properties if provided
                    if summary:
                        component['summary'] = summary
                        
                    if start_time:
                        component['dtstart'] = start_time
                        
                    if end_time:
                        component['dtend'] = end_time
                        
                    if description:
                        component['description'] = description
                        
                    if location:
                        component['location'] = location
                        
                    # Update last modified timestamp
                    component['last-modified'] = datetime.now(pytz.utc)
                
                # Save the updated event
                event.data = vcal.to_ical()
                event.save()
                
                logger.info(f"Updated event with UID: {uid}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    def get_free_busy(self, start_date, end_date):
        """Get free/busy information for the calendar."""
        try:
            if not self.ready:
                logger.warning("CalDAV server not ready, returning empty free/busy")
                return []
                
            # Get the default calendar
            calendar = self.get_default_calendar()
            if not calendar:
                logger.warning("No calendar available, returning empty free/busy")
                return []
                
            # Get the free/busy report
            free_busy = calendar.freebusy_report(start=start_date, end=end_date)
            
            # Format the busy times
            busy_times = []
            for period in free_busy:
                busy_times.append({
                    'start': period[0],
                    'end': period[1]
                })
                
            return busy_times
            
        except Exception as e:
            logger.error(f"Error getting free/busy: {e}")
            return []
    
    def get_available_slots(self, date, duration=30, start_hour=9, end_hour=17):
        """Get available time slots for a specific date."""
        try:
            if not self.ready:
                logger.warning("CalDAV server not ready, returning empty slots")
                return []
                
            # Create datetime range for the entire day
            start_date = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
            end_date = datetime.combine(date, datetime.min.time().replace(hour=end_hour))
            
            # Get busy periods
            busy_periods = self.get_free_busy(start_date, end_date)
            
            # Initialize all slots as available
            slot_duration = timedelta(minutes=duration)
            available_slots = []
            
            current_slot = start_date
            while current_slot + slot_duration <= end_date:
                # Check if the slot overlaps with any busy period
                is_available = True
                for period in busy_periods:
                    slot_end = current_slot + slot_duration
                    if (current_slot < period['end'] and slot_end > period['start']):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        'start': current_slot,
                        'end': current_slot + slot_duration
                    })
                
                # Move to the next slot
                current_slot += slot_duration
                
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
