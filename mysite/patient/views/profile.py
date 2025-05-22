# patient/views/profile.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.profile_service import ProfileService
from patient.utils import get_current_patient
from patient.forms import SecurePatientProfileEditForm as PatientProfileEditForm

logger = logging.getLogger(__name__)

@patient_required
def patient_profile(request):
    """
    Patient profile view with edit functionality.
    Uses service layer for data management and form processing.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process profile update via service
            result = ProfileService.update_patient_profile(
                patient_id=patient.id,
                form_data=request.POST,
                user=request.user
            )
            
            if result.get('success', False):
                messages.success(request, "Profile updated successfully!")
                # Refresh patient_dict with updated data
                _, patient_dict = get_current_patient(request)  
            else:
                messages.error(request, result.get('error', "Error updating profile."))
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            messages.error(request, f"Error updating profile: {str(e)}")
    
    # For GET requests or after POST, prepare the form with current data
    try:
        # Get form with current data from service
        form_data = ProfileService.get_profile_form_data(patient.id)
        
        if not form_data.get('success', False):
            messages.error(request, form_data.get('error', "Error loading profile data."))
        
        form = form_data.get('form')
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'form': form,
            'active_section': 'profile',
        }
    except Exception as e:
        logger.error(f"Error loading profile data: {str(e)}")
        # Create a default form as fallback
        initial_data = {
            'first_name': patient.user.first_name,
            'last_name': patient.user.last_name,
            'email': patient.user.email,
        }
        form = PatientProfileEditForm(instance=patient, initial=initial_data)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'form': form,
            'active_section': 'profile',
        }
        messages.error(request, "There was an error loading your profile data.")
    
    return render(request, "patient/profile.html", context)

@patient_required
def patient_medical_history(request):
    """
    Patient medical history view showing comprehensive health record.
    Uses service layer for data retrieval and formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get medical history from service
        history_data = ProfileService.get_medical_history(patient.id)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'active_section': 'medical_history',
            'medical_history': history_data.get('medical_history', {})
        }
    except Exception as e:
        logger.error(f"Error retrieving medical history: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'active_section': 'medical_history',
            'medical_history': {}
        }
        messages.error(request, "There was an error loading your medical history.")
    
    return render(request, "patient/medical_history.html", context)
