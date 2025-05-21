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
def get_current_patient(request):
    """
    Get the current patient object and dictionary representation
    
    Args:
        request: HttpRequest object
        
    Returns:
        tuple: (patient, patient_dict) or (None, None) if not found
    """
    if not hasattr(request, 'patient'):
        return None, None
    
    patient = request.patient
    
    # Create a dictionary representation (useful for templates)
    patient_dict = {
        'id': patient.id,
        'full_name': patient.full_name,
        'first_name': patient.user.first_name,
        'last_name': patient.user.last_name,
        'email': patient.user.email,
        'date_of_birth': patient.date_of_birth,
        'ohip_number': patient.ohip_number,
        'primary_phone': patient.primary_phone,
        'alternate_phone': patient.alternate_phone,
        'address': patient.address,
        'emergency_contact_name': patient.emergency_contact_name,
        'emergency_contact_phone': patient.emergency_contact_phone
    }
    
    return patient, patient_dict
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
