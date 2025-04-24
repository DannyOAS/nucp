from caldav import DAVClient
from datetime import datetime, timedelta
import vobject
import logging
from theme_name.repositories import AppointmentRepository  # Assuming use of existing repo

logger = logging.getLogger(__name__)

class CalendarService:
    """Service to interact with a CalDAV calendar (SOGo)."""

    def __init__(self, url, username, password):
        self.client = DAVClient(url=url, username=username, password=password)
        self.calendar = self.client.principal().calendars()[0]  # Assumes single calendar

    def list_upcoming_events(self, days=7):
        """List events in the next `days` days."""
        try:
            now = datetime.now()
            future = now + timedelta(days=days)
            events = self.calendar.date_search(start=now, end=future)
            return [
                {
                    'summary': e.vobject_instance.vevent.summary.value,
                    'start': e.vobject_instance.vevent.dtstart.value,
                    'end': e.vobject_instance.vevent.dtend.value,
                    'uid': e.vobject_instance.vevent.uid.value
                }
                for e in events
            ]
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return []

    def create_event(self, summary, start_time, end_time, description=None, uid=None):
        """Create a new calendar event."""
        try:
            vcal = vobject.iCalendar()
            vevent = vcal.add('vevent')
            vevent.add('summary').value = summary
            vevent.add('dtstart').value = start_time
            vevent.add('dtend').value = end_time
            vevent.add('uid').value = uid or f"django-{int(datetime.timestamp(start_time))}"
            if description:
                vevent.add('description').value = description
            self.calendar.add_event(vcal.serialize())
            return True
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return False

    def delete_event(self, uid):
        """Delete an event by UID."""
        try:
            events = self.calendar.events()
            for event in events:
                if event.vobject_instance.vevent.uid.value == uid:
                    event.delete()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False

    def sync_appointment_to_calendar(self, appointment_id):
        """Create a calendar event from a Django appointment."""
        try:
            appt = AppointmentRepository.get_by_id(appointment_id)
            if not appt:
                logger.warning(f"Appointment ID {appointment_id} not found")
                return False

            summary = f"Appointment with {appt.get('doctor')}"
            start_time = self._parse_time(appt.get('time'))
            end_time = start_time + timedelta(minutes=30)
            uid = f"django-appt-{appointment_id}"

            return self.create_event(summary, start_time, end_time, description=appt.get('reason'), uid=uid)
        except Exception as e:
            logger.error(f"Error syncing appointment {appointment_id}: {e}")
            return False

    def _parse_time(self, time_str):
        """Helper to parse time string to datetime."""
        try:
            return datetime.strptime(time_str, '%b %d, %Y - %I:%M %p')
        except ValueError:
            logger.error(f"Time parse failed for: {time_str}")
            return datetime.now()
