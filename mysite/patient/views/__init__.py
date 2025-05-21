# patient/views/__init__.py
from .dashboard import patient_dashboard
from .appointments import appointments_view, schedule_appointment, reschedule_appointment, cancel_appointment
from .prescriptions import patient_prescriptions, request_prescription, request_refill, prescription_detail

# Import all email-related views
from .email import email_view, compose_email, email_folder, view_email, email_action

from .profile import patient_profile, patient_medical_history
from .video import jitsi_video_view, join_video_appointment
from .help import patient_help_center
from .search import patient_search
