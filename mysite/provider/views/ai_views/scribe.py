# provider/views/ai_views/scribe.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import logging
import requests

from theme_name.repositories import ProviderRepository
from provider.services import AIScribeService
from provider.models import RecordingSession, ClinicalNote
from provider.utils import get_current_provider

logger = logging.getLogger(__name__)

@login_required
def ai_scribe_dashboard(request):
    """AI scribe dashboard view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get AI scribe data for this provider
        recordings = RecordingSession.objects.filter(
            provider=provider
        ).order_by('-start_time')[:10]
        
        notes = ClinicalNote.objects.filter(
            provider=provider
        ).order_by('-created_at')[:10]
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/ai-scribe/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     api_data = response.json()
        #     recordings = api_data.get('recordings', [])
        #     notes = api_data.get('notes', [])
        # else:
        #     recordings = []
        #     notes = []
        #     messages.error(request, "Error retrieving AI Scribe data.")
    except Exception as e:
        logger.error(f"Error loading AI Scribe dashboard: {str(e)}")
        recordings = []
        notes = []
        messages.error(request, f"Error loading AI Scribe dashboard: {str(e)}")
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'recordings': recordings,
        'notes': notes,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/ai_scribe_dashboard.html", context)

@login_required
@require_POST
def start_recording(request):
    """Start a recording session with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
    
    appointment_id = request.POST.get('appointment_id')
    
    try:
        recording = AIScribeService.start_recording(provider.id, appointment_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/ai-scribe/recordings/')
        # response = requests.post(api_url, json={'appointment_id': appointment_id})
        # if response.status_code == 201:  # Created
        #     recording_data = response.json()
        #     return JsonResponse({
        #         'success': True,
        #         'recording_id': recording_data.get('id'),
        #         'message': 'Recording started successfully.'
        #     })
        # else:
        #     return JsonResponse({
        #         'success': False,
        #         'message': 'Error starting recording through API.'
        #     }, status=500)
        
        return JsonResponse({
            'success': True,
            'recording_id': recording.id,
            'message': 'Recording started successfully.'
        })
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error starting recording: {str(e)}'
        }, status=500)

@login_required
@require_POST
def stop_recording(request):
    """Stop a recording session with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
    
    recording_id = request.POST.get('recording_id')
    
    try:
        # Verify this recording belongs to this provider
        recording = get_object_or_404(RecordingSession, id=recording_id, provider=provider)
        
        result = AIScribeService.stop_recording(recording_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/ai-scribe/recordings/{recording_id}/stop/')
        # response = requests.post(api_url)
        # if response.status_code == 200:
        #     result = response.json()
        # else:
        #     return JsonResponse({
        #         'success': False,
        #         'message': 'Error stopping recording through API.'
        #     }, status=500)
        
        return JsonResponse({
            'success': True,
            'transcription_status': result.get('transcription_status'),
            'message': 'Recording stopped successfully.'
        })
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error stopping recording: {str(e)}'
        }, status=500)

@login_required
def get_transcription(request, recording_id):
    """Get transcription for a recording with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Verify this recording belongs to this provider
        recording = get_object_or_404(RecordingSession, id=recording_id, provider=provider)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/ai-scribe/recordings/{recording_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     recording_data = response.json()
        # else:
        #     messages.error(request, "Error retrieving transcription.")
        #     return redirect('ai_scribe_dashboard')
        
        # Format recording data for the template
        recording_data = {
            'id': recording.id,
            'appointment_id': recording.appointment.id if recording.appointment else None,
            'patient_name': recording.appointment.patient.get_full_name() if recording.appointment and recording.appointment.patient else "Unknown",
            'start_time': recording.start_time.strftime('%B %d, %Y - %I:%M %p'),
            'end_time': recording.end_time.strftime('%B %d, %Y - %I:%M %p') if recording.end_time else None,
            'duration': (recording.end_time - recording.start_time).total_seconds() // 60 if recording.end_time else None,
            'status': recording.transcription_status,
            'transcription_text': recording.transcription_text
        }
    except Exception as e:
        logger.error(f"Error retrieving transcription: {str(e)}")
        messages.error(request, f"Error retrieving transcription: {str(e)}")
        return redirect('ai_scribe_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'recording': recording_data,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/transcription.html", context)

@login_required
@require_POST
def generate_clinical_note(request, transcription_id):
    """Generate clinical note from transcription with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
    
    try:
        # Verify this recording belongs to this provider
        recording = get_object_or_404(RecordingSession, id=transcription_id, provider=provider)
        
        note = AIScribeService.generate_note(recording.id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/ai-scribe/recordings/{transcription_id}/generate-note/')
        # response = requests.post(api_url)
        # if response.status_code == 201:  # Created
        #     note_data = response.json()
        #     return JsonResponse({
        #         'success': True,
        #         'note_id': note_data.get('id'),
        #         'message': 'Clinical note generated successfully.'
        #     })
        # else:
        #     return JsonResponse({
        #         'success': False,
        #         'message': 'Error generating clinical note through API.'
        #     }, status=500)
        
        return JsonResponse({
            'success': True,
            'note_id': note.id,
            'message': 'Clinical note generated successfully.'
        })
    except Exception as e:
        logger.error(f"Error generating clinical note: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error generating note: {str(e)}'
        }, status=500)

@login_required
def view_clinical_note(request, note_id):
    """View clinical note with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Verify this note belongs to this provider
        note = get_object_or_404(ClinicalNote, id=note_id, provider=provider)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/ai-scribe/notes/{note_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     note_data = response.json()
        # else:
        #     messages.error(request, "Error retrieving clinical note.")
        #     return redirect('ai_scribe_dashboard')
        
        # Format note data for the template
# provider/views/ai_views/scribe.py (continued)
        # Format note data for the template
        note_data = {
            'id': note.id,
            'appointment_id': note.appointment.id if note.appointment else None,
            'patient_name': note.appointment.patient.get_full_name() if note.appointment and note.appointment.patient else "Unknown",
            'created_at': note.created_at.strftime('%B %d, %Y - %I:%M %p'),
            'updated_at': note.updated_at.strftime('%B %d, %Y - %I:%M %p'),
            'status': note.status,
            'ai_generated_text': note.ai_generated_text,
            'provider_edited_text': note.provider_edited_text
        }
    except Exception as e:
        logger.error(f"Error viewing clinical note: {str(e)}")
        messages.error(request, f"Error viewing clinical note: {str(e)}")
        return redirect('ai_scribe_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'note': note_data,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/view_clinical_note.html", context)

@login_required
def edit_clinical_note(request, note_id):
    """Edit clinical note with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Verify this note belongs to this provider
        note = get_object_or_404(ClinicalNote, id=note_id, provider=provider)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/ai-scribe/notes/{note_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     note_data = response.json()
        # else:
        #     messages.error(request, "Error retrieving clinical note.")
        #     return redirect('ai_scribe_dashboard')
        
        if request.method == 'POST':
            # Process form submission
            note.provider_edited_text = request.POST.get('content')
            note.status = request.POST.get('status', 'reviewed')
            note.last_edited_by = request.user
            note.save()
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/provider/ai-scribe/notes/{note_id}/')
            # update_data = {
            #     'provider_edited_text': request.POST.get('content'),
            #     'status': request.POST.get('status', 'reviewed')
            # }
            # response = requests.patch(api_url, json=update_data)
            # if response.status_code == 200:
            #     messages.success(request, "Clinical note updated successfully.")
            # else:
            #     messages.error(request, "Error updating clinical note.")
            
            messages.success(request, "Clinical note updated successfully.")
            
            # Redirect based on the status
            if note.status == 'finalized':
                if note.appointment:
                    return redirect('view_appointment', appointment_id=note.appointment.id)
                else:
                    return redirect('view_clinical_note', note_id=note.id)
            else:
                return redirect('view_clinical_note', note_id=note.id)
        
        # Format note data for the template
        note_data = {
            'id': note.id,
            'appointment_id': note.appointment.id if note.appointment else None,
            'patient_name': note.appointment.patient.get_full_name() if note.appointment and note.appointment.patient else "Unknown",
            'created_at': note.created_at.strftime('%B %d, %Y - %I:%M %p'),
            'updated_at': note.updated_at.strftime('%B %d, %Y - %I:%M %p'),
            'status': note.status,
            'ai_generated_text': note.ai_generated_text,
            'provider_edited_text': note.provider_edited_text or note.ai_generated_text  # Use AI text as starting point if no edits yet
        }
    except Exception as e:
        logger.error(f"Error editing clinical note: {str(e)}")
        messages.error(request, f"Error editing clinical note: {str(e)}")
        return redirect('ai_scribe_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'note': note_data,
        'active_section': 'ai_scribe'
    }
    
    return render(request, "provider/edit_clinical_note.html", context)
