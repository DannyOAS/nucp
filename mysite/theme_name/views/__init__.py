# Import all views for backward compatibility

# Main website views
from .main_views import home, about, contact, blog_list, blog_detail, privacy_policy, terms_of_use

# Registration views
from .registration_views import (
    registration_view, prescription_view, login_view, 
    register_selection, patient_registration, provider_registration, 
    registration_success, schedule_demo, logout_view
)

# Patient views
from .patient_views.dashboard import patient_dashboard
#from .patient_views.appointments import appointments_view
from .patient_views.appointments import (
    appointments_view, schedule_appointment, 
    reschedule_appointment, cancel_appointment
)
from .patient_views.prescriptions import (
    patient_prescriptions, request_prescription, request_refill, 
    prescription_detail
)
from .patient_views.profile import patient_profile, patient_medical_history, patient_help_center
from .patient_views.messages import (
    patient_messages, patient_sent_messages, patient_archived_messages,
    patient_view_message, patient_compose_message, patient_message_action, 
    email_view, patient_search
)
from .patient_views.video import jitsi_video_view

# Provider views
from .provider_views.dashboard import provider_dashboard
from .provider_views.patients import (
    provider_patients, add_patient, view_patient
)
from .provider_views.prescriptions import (
    provider_prescriptions, approve_prescription, review_prescription,
    create_prescription, edit_prescription
)
from .provider_views.profile import provider_profile, provider_settings, provider_help_support
from .provider_views.messages import (
    provider_messages, provider_sent_messages, provider_view_message,
    provider_compose_message, provider_message_action
)
from .provider_views.email import (
    provider_email,
    provider_view_message, 
    provider_compose_message,
    provider_message_action,
    load_templates
)
from .provider_views.video import provider_video_consultation
from .provider_views.appointments import (
    provider_appointments, schedule_appointment as provider_schedule_appointment,
    view_appointment, update_appointment_status, reschedule_appointment as provider_reschedule_appointment
)
# Admin views
from .admin_views.dashboard import admin_dashboard
from .admin_views.patients import admin_patients
from .admin_views.providers import admin_providers
from .admin_views.logs import admin_logs

# AI views
from .ai_views.config import ai_config_dashboard, edit_model_config
from .ai_views.scribe import (
    ai_scribe_dashboard, start_recording, stop_recording, 
    get_transcription, generate_clinical_note, view_clinical_note, 
    edit_clinical_note
)
from .ai_views.forms import (
    forms_dashboard, create_form, view_document, download_document_pdf,
    update_document_status, templates_dashboard, create_template, edit_template
)
