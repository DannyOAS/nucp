from .dashboard import patient_dashboard
from .appointments import appointments_view
from .prescriptions import (
    patient_prescriptions, request_prescription, request_refill, 
    prescription_detail
)
from .profile import patient_profile, patient_medical_history, patient_help_center
from .messages import (
    patient_messages, patient_sent_messages, patient_archived_messages,
    patient_view_message, patient_compose_message, patient_message_action, 
    email_view, patient_search
)
from .video import jitsi_video_view
