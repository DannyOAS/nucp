#from .dashboard import provider_dashboard
#from .patients import provider_patients, add_patient, view_patient
#from .prescriptions import (
#    provider_prescriptions, approve_prescription, review_prescription,
#    create_prescription, edit_prescription
#)
#from .profile import provider_profile, provider_settings, provider_help_support
#from .messages import (
#    provider_messages, provider_sent_messages, provider_view_message,
#    provider_compose_message, provider_message_action
#)
#from .email import (
#    provider_email, provider_view_message, provider_compose_message,
#    provider_message_action, load_templates
#)
#from .video import provider_video_consultation
#from .appointments import provider_appointments
# provider/views/__init__.py
from .dashboard import provider_dashboard
from .appointments import (
    provider_appointments,
    schedule_appointment,  # Make sure this is imported
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
from .messages import provider_messages, provider_sent_messages, provider_view_message, provider_compose_message, provider_message_action
from .email import provider_email, load_templates
from .video import provider_video_consultation
from .profile import provider_profile, provider_settings, provider_help_support
# Import AI and form related views if needed
from .ai_views.scribe import (
    ai_scribe_dashboard,
    start_recording,
    stop_recording,
    get_transcription,
    generate_clinical_note,
    view_clinical_note,
    edit_clinical_note
)
from .ai_views.forms import (
    forms_dashboard,
    create_form,
    view_document,
    download_document_pdf,
    update_document_status
)
