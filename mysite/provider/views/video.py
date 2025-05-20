# provider/views/video.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import logging

from provider.services import VideoService
from provider.utils import get_current_provider
from api.v1.provider.serializers import RecordingSessionSerializer, ClinicalNoteSerializer

logger = logging.getLogger(__name__)

@login_required
def provider_video_consultation(request):
    """Video consultation view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get video consultation data from service
        video_data = VideoService.get_provider_video_dashboard(provider.id)
        
        # Format appointments using API serializer if needed
        video_appointments = video_data.get('video_appointments', [])
        if hasattr(video_appointments, 'model'):
            serializer = AppointmentSerializer(video_appointments, many=True)
            video_data['video_appointments'] = serializer.data
        
        # Format recordings using API serializer if needed
        recent_recordings = video_data.get('recent_recordings', [])
        if hasattr(recent_recordings, 'model'):
            serializer = RecordingSessionSerializer(recent_recordings, many=True)
            video_data['recent_recordings'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'consultations',
            'video_appointments': video_data.get('video_appointments', []),
            'active_sessions': video_data.get('active_sessions', []),
            'recent_recordings': video_data.get('recent_recordings', [])
        }
    except Exception as e:
        logger.error(f"Error retrieving video consultation data: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'consultations',
            'video_appointments': [],
            'active_sessions': [],
            'recent_recordings': []
        }
    
    return render(request, 'provider/video_consultation.html', context)

@login_required
def start_recording(request, appointment_id):
    """Start a new recording session for an appointment"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Start recording using service
        result = VideoService.start_recording(
            appointment_id=appointment_id,
            provider_id=provider.id
        )
        
        if result.get('success', False):
            messages.success(request, "Recording started successfully.")
            return redirect('provider_video_consultation')
        else:
            messages.error(request, result.get('error', "Error starting recording."))
            return redirect('provider_video_consultation')
    except Exception as e:
        logger.error(f"Error starting recording: {str(e)}")
        messages.error(request, f"Error starting recording: {str(e)}")
        return redirect('provider_video_consultation')

@login_required
def stop_recording(request, recording_id):
    """Stop an active recording session"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Stop recording using service
        result = VideoService.stop_recording(
            recording_id=recording_id,
            provider_id=provider.id
        )
        
        if result.get('success', False):
            messages.success(request, "Recording stopped and transcription initiated.")
            return redirect('provider_video_consultation')
        else:
            messages.error(request, result.get('error', "Error stopping recording."))
            return redirect('provider_video_consultation')
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        messages.error(request, f"Error stopping recording: {str(e)}")
        return redirect('provider_video_consultation')

@login_required
def view_recording(request, recording_id):
    """View a recording and its transcription"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get recording data from service
        recording_data = VideoService.get_recording_details(
            recording_id=recording_id,
            provider_id=provider.id
        )
        
        if not recording_data.get('success', False):
            messages.error(request, recording_data.get('error', "Recording not found."))
            return redirect('provider_video_consultation')
        
        # Format recording using API serializer if needed
        recording = recording_data.get('recording')
        if recording and hasattr(recording, '__dict__'):
            serializer = RecordingSessionSerializer(recording)
            recording_data['recording'] = serializer.data
            
        # Format notes using API serializer if needed
        notes = recording_data.get('notes', [])
        if hasattr(notes, 'model'):
            serializer = ClinicalNoteSerializer(notes, many=True)
            recording_data['notes'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'consultations',
            'recording': recording_data.get('recording'),
            'notes': recording_data.get('notes', [])
        }
    except Exception as e:
        logger.error(f"Error viewing recording: {str(e)}")
        messages.error(request, f"Error viewing recording: {str(e)}")
        return redirect('provider_video_consultation')
    
    return render(request, 'provider/view_recording.html', context)

@login_required
def generate_clinical_note(request, recording_id):
    """Generate a clinical note from a recording"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Generate clinical note using service
        result = VideoService.generate_clinical_note(
            recording_id=recording_id,
            provider_id=provider.id
        )
        
        if result.get('success', False):
            messages.success(request, "Clinical note generated successfully. Please review and edit as needed.")
            return redirect('edit_clinical_note', note_id=result.get('note_id'))
        else:
            messages.error(request, result.get('error', "Error generating clinical note."))
            return redirect('view_recording', recording_id=recording_id)
    except Exception as e:
        logger.error(f"Error generating clinical note: {str(e)}")
        messages.error(request, f"Error generating clinical note: {str(e)}")
        return redirect('view_recording', recording_id=recording_id)

@login_required
def edit_clinical_note(request, note_id):
    """Edit a clinical note"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get clinical note data from service
        note_data = VideoService.get_clinical_note(
            note_id=note_id,
            provider_id=provider.id
        )
        
        if not note_data.get('success', False):
            messages.error(request, note_data.get('error', "Clinical note not found."))
            return redirect('provider_video_consultation')
        
        # Format note using API serializer if needed
        note = note_data.get('note')
        if note and hasattr(note, '__dict__'):
            serializer = ClinicalNoteSerializer(note)
            note_data['note'] = serializer.data
        
        if request.method == 'POST':
            # Update note using service
            update_data = {
                'provider_edited_text': request.POST.get('edited_text'),
                'status': request.POST.get('status')
            }
            
            result = VideoService.update_clinical_note(
                note_id=note_id,
                provider_id=provider.id,
                update_data=update_data,
                user=request.user
            )
            
            if result.get('success', False):
                messages.success(request, "Clinical note updated successfully.")
                
                if update_data['status'] == 'finalized':
                    # If note is finalized, redirect to appointment view
                    appointment_id = note_data.get('note', {}).get('appointment_id')
                    if appointment_id:
                        return redirect('view_appointment', appointment_id=appointment_id)
                
                # Redirect back to the view note page
                return redirect('view_clinical_note', note_id=note_id)
            else:
                messages.error(request, result.get('error', "Error updating clinical note."))
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'consultations',
            'note': note_data.get('note')
        }
    except Exception as e:
        logger.error(f"Error editing clinical note: {str(e)}")
        messages.error(request, f"Error editing clinical note: {str(e)}")
        return redirect('provider_video_consultation')
    
    return render(request, 'provider/edit_clinical_note.html', context)

@login_required
def view_clinical_note(request, note_id):
    """View a clinical note"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get clinical note data from service
        note_data = VideoService.get_clinical_note(
            note_id=note_id,
            provider_id=provider.id
        )
        
        if not note_data.get('success', False):
            messages.error(request, note_data.get('error', "Clinical note not found."))
            return redirect('provider_video_consultation')
        
        # Format note using API serializer if needed
        note = note_data.get('note')
        if note and hasattr(note, '__dict__'):
            serializer = ClinicalNoteSerializer(note)
            note_data['note'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'consultations',
            'note': note_data.get('note')
        }
    except Exception as e:
        logger.error(f"Error viewing clinical note: {str(e)}")
        messages.error(request, f"Error viewing clinical note: {str(e)}")
        return redirect('provider_video_consultation')
    
    return render(request, 'provider/view_clinical_note.html', context)
