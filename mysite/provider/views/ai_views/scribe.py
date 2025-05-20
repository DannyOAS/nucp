# provider/views/ai_views/scribe.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import logging

from provider.services import AIScribeService
from provider.utils import get_current_provider
from api.v1.provider.serializers import RecordingSessionSerializer, ClinicalNoteSerializer

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
        # Get AI scribe data from service
        scribe_data = AIScribeService.get_dashboard_data(provider.id)
        
        # Format recordings using API serializer if needed
        recordings = scribe_data.get('recordings', [])
        if hasattr(recordings, 'model'):
            serializer = RecordingSessionSerializer(recordings, many=True)
            scribe_data['recordings'] = serializer.data
        
        # Format notes using API serializer if needed
        notes = scribe_data.get('notes', [])
        if hasattr(notes, 'model'):
            serializer = ClinicalNoteSerializer(notes, many=True)
            scribe_data['notes'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'recordings': scribe_data.get('recordings', []),
            'notes': scribe_data.get('notes', []),
            'active_section': 'ai_scribe'
        }
    except Exception as e:
        logger.error(f"Error loading AI Scribe dashboard: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'recordings': [],
            'notes': [],
            'active_section': 'ai_scribe'
        }
        messages.error(request, f"Error loading AI Scribe dashboard: {str(e)}")
    
    return render(request, "provider/ai_views/ai_scribe_dashboard.html", context)

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
        # Start recording using service
        result = AIScribeService.start_recording(
            provider_id=provider.id,
            appointment_id=appointment_id
        )
        
        if result.get('success', False):
            return JsonResponse({
                'success': True,
                'recording_id': result.get('recording_id'),
                'message': 'Recording started successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('error', 'Error starting recording.')
            }, status=500)
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
        # Stop recording using service
        result = AIScribeService.stop_recording(
            provider_id=provider.id,
            recording_id=recording_id
        )
        
        if result.get('success', False):
            return JsonResponse({
                'success': True,
                'transcription_status': result.get('transcription_status'),
                'message': 'Recording stopped successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('error', 'Error stopping recording.')
            }, status=500)
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
        # Get transcription data from service
        transcription_data = AIScribeService.get_transcription(
            provider_id=provider.id,
            recording_id=recording_id
        )
        
        if not transcription_data.get('success', False):
            messages.error(request, transcription_data.get('error', "Error retrieving transcription."))
            return redirect('ai_scribe_dashboard')
        
        # Format recording data using serializer if needed
        recording = transcription_data.get('recording')
        if recording and hasattr(recording, '__dict__'):
            serializer = RecordingSessionSerializer(recording)
            transcription_data['recording'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'recording': transcription_data.get('recording_data'),
            'active_section': 'ai_scribe'
        }
    except Exception as e:
        logger.error(f"Error retrieving transcription: {str(e)}")
        messages.error(request, f"Error retrieving transcription: {str(e)}")
        return redirect('ai_scribe_dashboard')
    
    return render(request, "provider/ai_views/transcription.html", context)

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
        # Generate note using service
        result = AIScribeService.generate_note(
            provider_id=provider.id,
            recording_id=transcription_id
        )
        
        if result.get('success', False):
            return JsonResponse({
                'success': True,
                'note_id': result.get('note_id'),
                'message': 'Clinical note generated successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('error', 'Error generating clinical note.')
            }, status=500)
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
        # Get clinical note data from service
        note_data = AIScribeService.get_clinical_note(
            provider_id=provider.id,
            note_id=note_id
        )
        
        if not note_data.get('success', False):
            messages.error(request, note_data.get('error', "Error retrieving clinical note."))
            return redirect('ai_scribe_dashboard')
        
        # Format note data using serializer if needed
        note = note_data.get('note')
        if note and hasattr(note, '__dict__'):
            serializer = ClinicalNoteSerializer(note)
            note_data['note'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'note': note_data.get('note_data'),
            'active_section': 'ai_scribe'
        }
    except Exception as e:
        logger.error(f"Error viewing clinical note: {str(e)}")
        messages.error(request, f"Error viewing clinical note: {str(e)}")
        return redirect('ai_scribe_dashboard')
    
    return render(request, "provider/ai_views/view_clinical_note.html", context)

@login_required
def edit_clinical_note(request, note_id):
    """Edit clinical note with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get clinical note data from service
        note_data = AIScribeService.get_clinical_note(
            provider_id=provider.id,
            note_id=note_id
        )
        
        if not note_data.get('success', False):
            messages.error(request, note_data.get('error', "Error retrieving clinical note."))
            return redirect('ai_scribe_dashboard')
        
        # Format note data using serializer if needed
        note = note_data.get('note')
        if note and hasattr(note, '__dict__'):
            serializer = ClinicalNoteSerializer(note)
            note_data['note'] = serializer.data
        
        if request.method == 'POST':
            # Update note using service
            update_data = {
                'provider_edited_text': request.POST.get('content'),
                'status': request.POST.get('status', 'reviewed')
            }
            
            result = AIScribeService.update_clinical_note(
                provider_id=provider.id,
                note_id=note_id,
                update_data=update_data,
                user=request.user
            )
            
            if result.get('success', False):
                messages.success(request, "Clinical note updated successfully.")
                
                # Redirect based on the status
                if update_data['status'] == 'finalized':
                    note = note_data.get('note')
                    appointment_id = note.get('appointment_id') if isinstance(note, dict) else None
                    if appointment_id:
                        return redirect('view_appointment', appointment_id=appointment_id)
                
                return redirect('view_clinical_note', note_id=note_id)
            else:
                messages.error(request, result.get('error', "Error updating clinical note."))
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'note': note_data.get('note_data'),
            'active_section': 'ai_scribe'
        }
    except Exception as e:
        logger.error(f"Error editing clinical note: {str(e)}")
        messages.error(request, f"Error editing clinical note: {str(e)}")
        return redirect('ai_scribe_dashboard')
    
    return render(request, "provider/ai_views/edit_clinical_note.html", context)
