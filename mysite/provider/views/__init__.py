# provider/views/__init__.py

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
from .video import provider_video_consultation

# Import placeholder functions for views not yet fully implemented
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from provider.utils import get_current_provider

@login_required
def ai_scribe_dashboard(request):
    """AI Scribe dashboard with authenticated provider."""
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'message': 'AI Scribe is currently being updated.',
        'active_section': 'ai_scribe'
    }
    return render(request, "provider/dashboard.html", context)

@login_required
def forms_dashboard(request):
    """Forms dashboard with authenticated provider."""
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'message': 'Forms functionality is currently being updated.',
        'active_section': 'forms'
    }
    return render(request, "provider/dashboard.html", context)

# Authentication-aware placeholder functions for AI views
@login_required
def start_recording(request):
    """Start recording with authenticated provider."""
    get_current_provider(request)  # This will handle redirection if needed
    return redirect('provider_dashboard')

@login_required
def stop_recording(request):
    """Stop recording with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def get_transcription(request, recording_id):
    """Get transcription with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def generate_clinical_note(request, transcription_id):
    """Generate clinical note with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def view_clinical_note(request, note_id):
    """View clinical note with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def edit_clinical_note(request, note_id):
    """Edit clinical note with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

# Authentication-aware placeholder functions for Forms views
@login_required
def create_form(request, template_id):
    """Create form with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def view_document(request, document_id):
    """View document with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def download_document_pdf(request, document_id):
    """Download document PDF with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')

@login_required
def update_document_status(request, document_id):
    """Update document status with authenticated provider."""
    get_current_provider(request)
    return redirect('provider_dashboard')
