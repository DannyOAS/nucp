from .dashboard import provider_dashboard
from .patients import provider_patients, add_patient, view_patient
from .prescriptions import (
    provider_prescriptions, approve_prescription, review_prescription,
    create_prescription, edit_prescription
)
from .profile import provider_profile, provider_settings, provider_help_support
from .messages import (
    provider_messages, provider_sent_messages, provider_view_message,
    provider_compose_message, provider_message_action
)
from .video import provider_video_consultation
from .appointments import provider_appointments
