# patient/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from patient.models import Patient
import logging

logger = logging.getLogger(__name__)

def patient_required(view_func):
    """
    Decorator to ensure the user has a patient profile and is in the patients group.
    This should be used on all patient views.
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        # Check if user is in patients group
        if not request.user.groups.filter(name='patients').exists():
            messages.error(request, "You don't have permission to access this page.")
            logger.warning(f"User {request.user.username} attempted to access patient view without being in patients group")
            return redirect('unauthorized')
        
        # Check if user has a patient profile
        try:
            patient = request.user.patient_profile
            # Add patient to request for easy access in views
            request.patient = patient
            return view_func(request, *args, **kwargs)
        except Patient.DoesNotExist:
            messages.error(request, "Patient profile not found. Please contact support.")
            logger.error(f"User {request.user.username} is in patients group but has no patient profile")
            return redirect('unauthorized')
    
    return wrapped_view

def provider_or_patient_required(view_func):
    """
    Decorator for views that can be accessed by either providers or patients.
    Useful for shared views like messaging.
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if 'patients' in user_groups:
            try:
                request.patient = request.user.patient_profile
                request.user_type = 'patient'
            except Patient.DoesNotExist:
                messages.error(request, "Patient profile not found.")
                return redirect('unauthorized')
        elif 'providers' in user_groups:
            try:
                from provider.models import Provider
                request.provider = Provider.objects.get(user=request.user)
                request.user_type = 'provider'
            except Provider.DoesNotExist:
                messages.error(request, "Provider profile not found.")
                return redirect('unauthorized')
        else:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('unauthorized')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view
