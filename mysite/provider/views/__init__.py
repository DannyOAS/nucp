# provider/views/__init__.py
# Add these imports to provider/views/__init__.py
from .ai_views import config as ai_config_views
from .ai_views import forms as ai_forms_views
from .ai_views import scribe as ai_scribe_views
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

# AI Scribe dashboard view
@login_required
def ai_scribe_dashboard(request):
    """AI Scribe dashboard with authenticated provider."""
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get recent recordings
    try:
        from provider.models import RecordingSession
        recent_recordings = RecordingSession.objects.filter(
            provider=provider
        ).order_by('-start_time')[:5]
        
        # Format for template
        recordings_list = []
        for recording in recent_recordings:
            recordings_list.append({
                'id': recording.id,
                'appointment_id': recording.appointment.id if recording.appointment else None,
                'patient_name': recording.appointment.patient.get_full_name() if recording.appointment and recording.appointment.patient else "Unknown",
                'start_time': recording.start_time.strftime('%B %d, %Y - %I:%M %p'),
                'duration': (recording.end_time - recording.start_time).total_seconds() // 60 if recording.end_time else None,
                'status': recording.transcription_status
            })
    except Exception as e:
        logger.error(f"Error retrieving recent recordings: {str(e)}")
        recordings_list = []
        
    # Get recent clinical notes
    try:
        from provider.models import ClinicalNote
        recent_notes = ClinicalNote.objects.filter(
            provider=provider
        ).order_by('-created_at')[:5]
        
        notes_list = []
        for note in recent_notes:
            notes_list.append({
                'id': note.id,
                'patient_name': note.appointment.patient.get_full_name() if note.appointment and note.appointment.patient else "Unknown",
                'created_at': note.created_at.strftime('%B %d, %Y'),
                'status': note.status
            })
    except Exception as e:
        logger.error(f"Error retrieving recent clinical notes: {str(e)}")
        notes_list = []
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'recent_recordings': recordings_list,
        'recent_notes': notes_list,
        'active_section': 'ai_scribe'
    }
    return render(request, "provider/ai_scribe_dashboard.html", context)

# Forms dashboard view
@login_required
def forms_dashboard(request):
    """Forms dashboard with authenticated provider."""
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get available document templates
    try:
        from provider.models import DocumentTemplate, GeneratedDocument
        templates = DocumentTemplate.objects.filter(is_active=True)
        
        # Get recent generated documents
        recent_documents = GeneratedDocument.objects.filter(
            provider=provider
        ).order_by('-created_at')[:5]
        
        docs_list = []
        for doc in recent_documents:
            docs_list.append({
                'id': doc.id,
                'template_name': doc.template.name if doc.template else "Unknown",
                'patient_name': doc.patient.get_full_name() if doc.patient else "Unknown",
                'created_at': doc.created_at.strftime('%B %d, %Y'),
                'status': doc.status
            })
    except Exception as e:
        logger.error(f"Error retrieving forms data: {str(e)}")
        templates = []
        docs_list = []
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'templates': templates,
        'recent_documents': docs_list,
        'active_section': 'forms'
    }
    return render(request, "provider/forms_dashboard.html", context)

# Forms-related views
@login_required
def create_form(request, template_id):
    """Create a new form from a template"""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        from provider.models import DocumentTemplate
        template = DocumentTemplate.objects.get(id=template_id, is_active=True)
        
        if request.method == 'POST':
            # Process form data
            patient_id = request.POST.get('patient_id')
            form_data = request.POST.dict()
            
            # Create document
            from provider.models import GeneratedDocument
            from django.contrib.auth.models import User
            
            document = GeneratedDocument.objects.create(
                patient=User.objects.get(id=patient_id),
                provider=provider,
                template=template,
                document_data=form_data,
                status='draft',
                created_by=request.user
            )
            
            return redirect('view_document', document_id=document.id)
        
        # Get patients for template
# provider/views/__init__.py (continued)
        # Get patients for template
        from theme_name.models import PatientRegistration
        if hasattr(PatientRegistration, 'provider'):
            patients = PatientRegistration.objects.filter(provider=provider)
        else:
            from common.models import Appointment
            patient_ids = Appointment.objects.filter(
                doctor=provider
            ).values_list('patient_id', flat=True).distinct()
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
    except DocumentTemplate.DoesNotExist:
        messages.error(request, "Template not found.")
        return redirect('forms_dashboard')
    except Exception as e:
        logger.error(f"Error creating form: {str(e)}")
        messages.error(request, f"Error creating form: {str(e)}")
        return redirect('forms_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'template': template,
        'patients': patients,
        'active_section': 'forms'
    }
    
    return render(request, "provider/create_form.html", context)

@login_required
def view_document(request, document_id):
    """View a generated document"""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        from provider.models import GeneratedDocument
        document = GeneratedDocument.objects.get(id=document_id, provider=provider)
        
        # Format for template
        document_data = {
            'id': document.id,
            'template_name': document.template.name if document.template else "Unknown",
            'patient_name': document.patient.get_full_name() if document.patient else "Unknown",
            'created_at': document.created_at.strftime('%B %d, %Y'),
            'status': document.status,
            'content': document.rendered_content or "Preview not available"
        }
    except GeneratedDocument.DoesNotExist:
        messages.error(request, "Document not found.")
        return redirect('forms_dashboard')
    except Exception as e:
        logger.error(f"Error viewing document: {str(e)}")
        messages.error(request, f"Error viewing document: {str(e)}")
        return redirect('forms_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'document': document_data,
        'active_section': 'forms'
    }
    
    return render(request, "provider/view_document.html", context)

@login_required
def download_document_pdf(request, document_id):
    """Download a document as PDF"""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    try:
        from provider.models import GeneratedDocument
        document = GeneratedDocument.objects.get(id=document_id, provider=provider)
        
        # Generate PDF if not already generated
        if not document.pdf_storage_path:
            # In a real app, this would generate a PDF and update the storage path
            # For now, just update the status
            document.status = 'approved'
            document.save()
            
            messages.warning(request, "PDF generation is not fully implemented yet.")
            return redirect('view_document', document_id=document_id)
        
        # In a real app, this would serve the PDF file
        messages.info(request, "PDF download would start here in the production version.")
        return redirect('view_document', document_id=document_id)
    except GeneratedDocument.DoesNotExist:
        messages.error(request, "Document not found.")
        return redirect('forms_dashboard')
    except Exception as e:
        logger.error(f"Error downloading document: {str(e)}")
        messages.error(request, f"Error downloading document: {str(e)}")
        return redirect('view_document', document_id=document_id)

@login_required
def update_document_status(request, document_id):
    """Update the status of a document"""
    provider, provider_dict = get_current_provider(request)
    
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status not in ['draft', 'pending_approval', 'approved', 'sent', 'archived']:
            messages.error(request, "Invalid document status.")
            return redirect('view_document', document_id=document_id)
        
        try:
            from provider.models import GeneratedDocument
            document = GeneratedDocument.objects.get(id=document_id, provider=provider)
            
            # Update status
            document.status = status
            
            # If approved, set approved_by
            if status == 'approved':
                document.approved_by = request.user
            
            document.save()
            
            messages.success(request, f"Document status updated to {status}.")
        except GeneratedDocument.DoesNotExist:
            messages.error(request, "Document not found.")
            return redirect('forms_dashboard')
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            messages.error(request, f"Error updating document status: {str(e)}")
    
    return redirect('view_document', document_id=document_id)
