# provider/views/video.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
import requests

from common.services import VideoService
from theme_name.data_access import get_provider_appointments
from provider.utils import get_current_provider
from provider.models import RecordingSession

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
        # Get appointments for this provider
        all_appointments = get_provider_appointments(provider.id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/appointments/')
        # params = {
        #     'type': 'Virtual',
        #     'status': 'Scheduled'
        # }
        # response = requests.get(api_url, params=params)
        # if response.status_code == 200:
        #     all_appointments = response.json()
        # else:
        #     all_appointments = []
        
        # Filter for virtual appointments
        video_appointments = [a for a in all_appointments if a.get('type') == 'Virtual']
        
        # Get any active video sessions
        active_sessions = []
        try:
            if 'get_active_sessions' in dir(VideoService):
                active_sessions = VideoService.get_active_sessions(provider.id)
                
                # API version (commented out for now):
                # api_url = request.build_absolute_uri('/api/provider/video-sessions/active/')
                # response = requests.get(api_url)
                # if response.status_code == 200:
                #     active_sessions = response.json()
                # else:
                #     active_sessions = []
        except Exception as e:
            logger.error(f"Error retrieving active video sessions: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving video appointments: {str(e)}")
        video_appointments = []
        active_sessions = []
    
    # Get recent recordings
    try:
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
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'consultations',
        'video_appointments': video_appointments,
        'active_sessions': active_sessions,
        'recent_recordings': recordings_list
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
        # Get the appointment
        from common.models import Appointment
        appointment = Appointment.objects.get(id=appointment_id, doctor=provider)
        
        # Create a new recording session
        recording = RecordingSession.objects.create(
            appointment=appointment,
            provider=provider,
            transcription_status='pending'
        )
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/appointments/{appointment_id}/start-recording/')
        # response = requests.post(api_url)
        # if response.status_code == 201:  # Created
        #     recording = response.json()
        #     messages.success(request, "Recording started successfully.")
        # else:
        #     messages.error(request, "Error starting recording.")
        #     return redirect('provider_video_consultation')
        
        messages.success(request, "Recording started successfully.")
        
        # Redirect to the consultation view
        return redirect('provider_video_consultation')
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
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
        # Get the recording session
        recording = RecordingSession.objects.get(id=recording_id, provider=provider)
        
        # Update the recording session
        recording.end_time = timezone.now()
        recording.transcription_status = 'in_progress'
        recording.save()
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/recordings/{recording_id}/stop/')
        # response = requests.post(api_url)
        # if response.status_code == 200:
        #     messages.success(request, "Recording stopped and transcription initiated.")
        # else:
        #     messages.error(request, "Error stopping recording.")
        
        messages.success(request, "Recording stopped and transcription initiated.")
        
        # Redirect to the consultation view
        return redirect('provider_video_consultation')
    except RecordingSession.DoesNotExist:
        messages.error(request, "Recording session not found.")
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
        # Get the recording session
        recording = RecordingSession.objects.get(id=recording_id, provider=provider)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/recordings/{recording_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     recording_data = response.json()
        # else:
        #     messages.error(request, "Recording not found.")
        #     return redirect('provider_video_consultation')
        
        # Format for template
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
        
        # Get any clinical notes generated from this recording
        from provider.models import ClinicalNote
        notes = ClinicalNote.objects.filter(transcription=recording).order_by('-created_at')
        
        notes_list = []
        for note in notes:
            notes_list.append({
                'id': note.id,
                'status': note.status,
                'created_at': note.created_at.strftime('%B %d, %Y - %I:%M %p'),
                'ai_generated_text': note.ai_generated_text[:200] + ('...' if len(note.ai_generated_text) > 200 else ''),
                'provider_edited_text': note.provider_edited_text[:200] + ('...' if len(note.provider_edited_text) > 200 else '')
            })
        
    except RecordingSession.DoesNotExist:
        messages.error(request, "Recording session not found.")
        return redirect('provider_video_consultation')
    except Exception as e:
        logger.error(f"Error viewing recording: {str(e)}")
        messages.error(request, f"Error viewing recording: {str(e)}")
        return redirect('provider_video_consultation')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'consultations',
        'recording': recording_data,
        'notes': notes_list
    }
    
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
        # Get the recording session
        recording = RecordingSession.objects.get(id=recording_id, provider=provider)
        
        # Check if transcription is complete
        if recording.transcription_status != 'completed':
            messages.error(request, "Transcription is not yet complete. Please wait for the transcription to finish.")
            return redirect('view_recording', recording_id=recording_id)
        
        # Create a new clinical note
        from provider.models import ClinicalNote
        note = ClinicalNote.objects.create(
            appointment=recording.appointment,
            provider=provider,
            transcription=recording,
            status='draft'
        )
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/recordings/{recording_id}/generate-note/')
        # response = requests.post(api_url)
        # if response.status_code == 201:  # Created
        #     note_data = response.json()
        #     note_id = note_data.get('id')
        #     messages.success(request, "Clinical note generation initiated.")
        #     return redirect('edit_clinical_note', note_id=note_id)
        # else:
        #     messages.error(request, "Error generating clinical note.")
        #     return redirect('view_recording', recording_id=recording_id)
        
        # Simulate AI generation of note - in a real app, this would be done async
        note.ai_generated_text = f"AI-generated clinical note based on transcription of session {recording_id}.\n\n"
        note.ai_generated_text += "Patient: " + (recording.appointment.patient.get_full_name() if recording.appointment and recording.appointment.patient else "Unknown") + "\n\n"
        note.ai_generated_text += "Transcription excerpt:\n" + recording.transcription_text[:500] + "...\n\n"
        note.ai_generated_text += "Assessment and Plan:\n- Follow-up in 2 weeks\n- Continue current medications\n- Labs ordered"
        
        note.status = 'generated'
        note.save()
        
        messages.success(request, "Clinical note generated successfully. Please review and edit as needed.")
        
        return redirect('edit_clinical_note', note_id=note.id)
    except RecordingSession.DoesNotExist:
        messages.error(request, "Recording session not found.")
        return redirect('provider_video_consultation')
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
        # Get the clinical note
        from provider.models import ClinicalNote
        note = ClinicalNote.objects.get(id=note_id, provider=provider)
        
        if request.method == 'POST':
            # Update the note with provider edits
            edited_text = request.POST.get('edited_text')
            status = request.POST.get('status')
            
            note.provider_edited_text = edited_text
            note.status = status
            note.last_edited_by = request.user
            note.save()
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/provider/clinical-notes/{note_id}/')
            # update_data = {
            #     'provider_edited_text': edited_text,
            #     'status': status
            # }
            # response = requests.patch(api_url, json=update_data)
            # if response.status_code == 200:
            #     messages.success(request, "Clinical note updated successfully.")
            # else:
            #     messages.error(request, "Error updating clinical note.")
            
            messages.success(request, "Clinical note updated successfully.")
            
            if status == 'finalized':
                # Redirect to the appointment view
                return redirect('view_appointment', appointment_id=note.appointment.id)
            
            # Redirect back to the same page
            return redirect('edit_clinical_note', note_id=note_id)
        
        # Format for template
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
        
    except ClinicalNote.DoesNotExist:
        messages.error(request, "Clinical note not found.")
        return redirect('provider_video_consultation')
    except Exception as e:
        logger.error(f"Error editing clinical note: {str(e)}")
        messages.error(request, f"Error editing clinical note: {str(e)}")
        return redirect('provider_video_consultation')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'consultations',
        'note': note_data
    }
    
    return render(request, 'provider/edit_clinical_note.html', context)
