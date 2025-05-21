# patient/views/__init__.py
from .dashboard import patient_dashboard
from .appointments import appointments_view, schedule_appointment, reschedule_appointment, cancel_appointment
from .prescriptions import patient_prescriptions, request_prescription, request_refill, prescription_detail

# Removed message-related imports

from .profile import patient_profile, patient_medical_history
from .video import jitsi_video_view
from .email import email_view
from .help import patient_help_center
from .search import patient_search
