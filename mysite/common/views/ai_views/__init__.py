from .config import ai_config_dashboard, edit_model_config
from .scribe import (
    ai_scribe_dashboard, start_recording, stop_recording, 
    get_transcription, generate_clinical_note, view_clinical_note, 
    edit_clinical_note
)
from .forms import (
    forms_dashboard, create_form, view_document, download_document_pdf,
    update_document_status, templates_dashboard, create_template, edit_template
)
