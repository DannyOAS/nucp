from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from theme_name.repositories import ProviderRepository
from common.services import AIScribeService
from provider.models import RecordingSession, ClinicalNote

def ai_scribe_dashboard(request):
    """AI scribe dashboard view"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get AI scribe data
    recordings = RecordingSession.objects.all().order_by('-start_time')[:10]
    notes = ClinicalNote.objects.all().order_by('-created_at')[:10]
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'recordings': recordings,
        'notes': notes,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/ai_scribe_dashboard.html", context)

@require_POST
def start_recording(request):
    """Start a recording session"""
    provider_id = 1  # In production, get from request.user
    appointment_id = request.POST.get('appointment_id')
    
    try:
        recording = AIScribeService.start_recording(provider_id, appointment_id)
        return JsonResponse({
            'success': True,
            'recording_id': recording.id,
            'message': 'Recording started successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error starting recording: {str(e)}'
        }, status=500)

@require_POST
def stop_recording(request):
    """Stop a recording session"""
    recording_id = request.POST.get('recording_id')
    
    try:
        result = AIScribeService.stop_recording(recording_id)
        return JsonResponse({
            'success': True,
            'transcription_status': result.get('transcription_status'),
            'message': 'Recording stopped successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error stopping recording: {str(e)}'
        }, status=500)

def get_transcription(request, recording_id):
    """Get transcription for a recording"""
    recording = get_object_or_404(RecordingSession, id=recording_id)
    
    context = {
        'recording': recording,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/transcription.html", context)

@require_POST
def generate_clinical_note(request, transcription_id):
    """Generate clinical note from transcription"""
    recording = get_object_or_404(RecordingSession, id=transcription_id)
    
    try:
        note = AIScribeService.generate_note(recording.id)
        return JsonResponse({
            'success': True,
            'note_id': note.id,
            'message': 'Clinical note generated successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating note: {str(e)}'
        }, status=500)

def view_clinical_note(request, note_id):
    """View clinical note"""
    note = get_object_or_404(ClinicalNote, id=note_id)
    
    context = {
        'note': note,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/view_clinical_note.html", context)

def edit_clinical_note(request, note_id):
    """Edit clinical note"""
    note = get_object_or_404(ClinicalNote, id=note_id)
    
    if request.method == 'POST':
        # Process form submission
        note.provider_edited_text = request.POST.get('content')
        note.status = 'reviewed'
        note.last_edited_by = request.user
        note.save()
        
        messages.success(request, "Clinical note updated successfully.")
        return redirect('view_clinical_note', note_id=note.id)
    
    context = {
        'note': note,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/edit_clinical_note.html", context)
