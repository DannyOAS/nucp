# provider/views/__init__.py
# Import views from AI modules
from .ai_views import config as ai_views_config
from .ai_views import forms as ai_views_forms
from .ai_views import scribe as ai_views_scribe

# Import views from their respective modules
from .dashboard import provider_dashboard
from .appointments import (
    provider_appointments,
    schedule_appointment,
    view_appointment, 
    get_appointment_date, 
    process_appointments_for_calendar,
    reschedule_appointment,
    update_appointment_status
)
from .patients import provider_patients, add_patient, view_patient
from .prescriptions import (
    provider_prescriptions,
    approve_prescription,
    review_prescription,
    create_prescription,
    edit_prescription
)
from .email import (
    provider_email, 
    provider_compose_message, 
    provider_message_action, 
    provider_view_message, 
    load_templates
)
from .profile import provider_profile, provider_settings, provider_help_support
from .video import (
    provider_video_consultation,
    start_recording,
    stop_recording,
    view_recording,
    generate_clinical_note,
    edit_clinical_note
)

# For backwards compatibility
# Export AI view namespaces
ai_views = {
    'config': ai_views_config,
    'forms': ai_views_forms,
    'scribe': ai_views_scribe,
}
