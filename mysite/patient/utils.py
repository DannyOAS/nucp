# patient/utils.py
"""
Patient utility functions.
This module contains utility functions for working with Patient objects,
including retrieving the current patient based on the authenticated user.
"""

import logging
from django.shortcuts import redirect
from django.contrib import messages
from patient.models import Patient

logger = logging.getLogger(__name__)

def get_current_patient(request, redirect_on_failure=True):
    """
    Get the Patient object for the currently authenticated user.
    
    This is the central function for retrieving the current patient.
    All patient views should use this function to ensure consistency.
    
    Args:
        request: The HTTP request object containing the authenticated user
        redirect_on_failure: Whether to redirect to unauthorized page if no patient is found
        
    Returns:
        Patient: The Patient model instance
            
    Note:
        If no patient is found and redirect_on_failure is True, this function
        will redirect to the 'unauthorized' view and not return.
    """
    user = request.user
    
    # Check if user is authenticated
    if not user.is_authenticated:
        logger.warning("Unauthenticated user attempting to access patient view")
        if redirect_on_failure:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('login')
        return None
    
    # Check if user is in patients group
    if not user.groups.filter(name='patients').exists():
        logger.warning(f"User {user.username} is not in patients group")
        if redirect_on_failure:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('unauthorized')
        return None
    
    try:
        # Get the patient associated with this user
        patient = Patient.objects.get(user=user)
        logger.info(f"Patient retrieved: ID {patient.id}, User: {user.username}")
        return patient
        
    except Patient.DoesNotExist:
        logger.warning(f"No Patient record found for authenticated user: {user.username}")
        
        if redirect_on_failure:
            messages.error(request, "Patient profile not found. Please contact support.")
            return redirect('unauthorized')
        return None
    
    except Exception as e:
        logger.error(f"Error retrieving patient: {str(e)}")
        if redirect_on_failure:
            messages.error(request, "There was an error retrieving your patient information.")
            return redirect('unauthorized')
        return None

def ensure_patient_profile(user):
    """
    Ensure a Patient profile exists for the given user.
    This is useful during transition from repository-based system.
    
    Args:
        user: Django User instance
        
    Returns:
        Patient: The Patient instance (existing or newly created)
    """
    if not user.groups.filter(name='patients').exists():
        return None
    
    try:
        return Patient.objects.get(user=user)
    except Patient.DoesNotExist:
        # For transition purposes, create a minimal patient profile
        # This should be temporary and removed once all patients are properly registered
        logger.warning(f"Creating temporary patient profile for user: {user.username}")
        
        from datetime import date
        temp_patient = Patient.objects.create(
            user=user,
            date_of_birth=date(1990, 1, 1),  # Placeholder
            ohip_number=f"TEMP{user.id}",  # Temporary number
            primary_phone="000-000-0000",  # Placeholder
            address="Address not provided",
            emergency_contact_name="Not provided",
            emergency_contact_phone="000-000-0000"
        )
        
        return temp_patient

def patient_required(view_func):
    """
    Decorator to ensure the user has a patient profile.
    Use this on views that require a patient profile.
    """
    def wrapped_view(request, *args, **kwargs):
        patient = get_current_patient(request)
        if patient:
            # Add patient to request for easy access in views
            request.patient = patient
            return view_func(request, *args, **kwargs)
        # If get_current_patient didn't redirect, do it here
        return redirect('unauthorized')
    
    return wrapped_view
