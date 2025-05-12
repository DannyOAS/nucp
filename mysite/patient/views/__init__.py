# patient/views/__init__.py
from .dashboard import patient_dashboard
from .appointments import appointments_view, schedule_appointment, reschedule_appointment, cancel_appointment
from .prescriptions import patient_prescriptions, request_prescription, request_refill, prescription_detail

# Comment out or remove the ones that don't exist yet
# from .messages import patient_messages, patient_sent_messages, patient_archived_messages, patient_view_message, patient_compose_message, patient_message_action
from .messages import patient_messages  # Only import what exists

from .profile import patient_profile, patient_medical_history
from .video import jitsi_video_view
from .email import email_view
from .help import patient_help_center
from .search import patient_search
