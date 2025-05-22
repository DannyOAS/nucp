# patient/views/appointments.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.appointment_service import AppointmentService
from patient.utils import get_current_patient
from api.v1.patient.serializers import AppointmentSerializer
from patient.models import Patient

logger = logging.getLogger(__name__)

@patient_required
def appointments_view(request):
    """
    Patient appointments view showing upcoming and past appointments.
    Uses service layer to retrieve data and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get appointments data from service
        appointments_data = AppointmentService.get_patient_appointments(patient.id)
        
        # Get healthcare providers from service - NEW
        provider_data = AppointmentService.get_patient_healthcare_providers(patient.id)
        
        # Format appointments using API serializer if needed
        upcoming_appointments = appointments_data.get('upcoming_appointments', [])
        if hasattr(upcoming_appointments, 'model'):
            serializer = AppointmentSerializer(upcoming_appointments, many=True)
            appointments_data['upcoming_appointments'] = serializer.data
        
        past_appointments = appointments_data.get('past_appointments', [])
        if hasattr(past_appointments, 'model'):
            serializer = AppointmentSerializer(past_appointments, many=True)
            appointments_data['past_appointments'] = serializer.data
        
        # Get healthcare providers from service response
        healthcare_providers = provider_data.get('healthcare_providers', [])
        providers_count = len(healthcare_providers)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'appointments': appointments_data.get('upcoming_appointments', []),
            'past_appointments': appointments_data.get('past_appointments', []),
            'healthcare_providers': healthcare_providers,  # From service
            'providers_count': providers_count,
            'today': appointments_data.get('today', None),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error retrieving appointments: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'appointments': [],
            'past_appointments': [],
            'healthcare_providers': [],  # Empty fallback
            'providers_count': 0,
            'today': None,
            'active_section': 'appointments'
        }
        messages.error(request, "There was an error loading your appointments. Please try again later.")
    
    return render(request, "patient/appointments.html", context)

@patient_required
def schedule_appointment(request):
    """
    View for patient to schedule a new appointment.
    Uses service layer for business logic and data retrieval.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process appointment creation via service
            result = AppointmentService.schedule_appointment(
                patient_id=patient.id,
                form_data=request.POST
            )
            
            if result.get('success', False):
                messages.success(request, "Appointment scheduled successfully!")
                return redirect('patient:patient_appointments')
            else:
                messages.error(request, result.get('error', "Error scheduling appointment."))
        except Exception as e:
            logger.error(f"Error scheduling appointment: {str(e)}")
            messages.error(request, f"Error scheduling appointment: {str(e)}")
    
    # For GET requests, prepare the scheduling form
    try:
        # Get form data from service
        form_data = AppointmentService.get_scheduling_form_data(patient.id)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'available_providers': form_data.get('available_providers', []),
            'available_dates': form_data.get('available_dates', []),
            'available_times': form_data.get('available_times', []),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error loading scheduling form: {str(e)}")
        # Default fallback data
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now().date()
        available_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(14)]
        available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'available_providers': [],
            'available_dates': available_dates,
            'available_times': available_times,
            'active_section': 'appointments'
        }
        messages.warning(request, "There was an issue loading available appointments. Using default options.")
    
    return render(request, "patient/schedule_appointment.html", context)

@patient_required
def reschedule_appointment(request, appointment_id):
    """
    View for patient to reschedule an existing appointment.
    Uses service layer for validation and business logic.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Verify appointment ownership and get details
        appointment_data = AppointmentService.get_appointment_for_reschedule(
            appointment_id=appointment_id,
            patient_id=patient.id
        )
        
        if not appointment_data.get('success', False):
            messages.error(request, appointment_data.get('error', "Appointment not found."))
            return redirect('patient:patient_appointments')
        
        # Format appointment data using serializer if needed
        appointment = appointment_data.get('appointment')
        if appointment and hasattr(appointment, '__dict__'):
            serializer = AppointmentSerializer(appointment)
            appointment = serializer.data
        
        if request.method == 'POST':
            # Process reschedule via service
            result = AppointmentService.reschedule_appointment(
                appointment_id=appointment_id,
                patient_id=patient.id,
                form_data=request.POST
            )
            
            if result.get('success', False):
                messages.success(request, "Appointment rescheduled successfully!")
                return redirect('patient:patient_appointments')
            else:
                messages.error(request, result.get('error', "Error rescheduling appointment."))
        
        # For GET requests, get available dates and times from service
        form_data = AppointmentService.get_scheduling_form_data(patient.id)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'appointment': appointment,
            'available_dates': form_data.get('available_dates', []),
            'available_times': form_data.get('available_times', []),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error processing appointment reschedule: {str(e)}")
        messages.error(request, "There was an error loading the appointment details.")
        return redirect('patient:patient_appointments')
    
    return render(request, "patient/reschedule_appointment.html", context)

@patient_required
def cancel_appointment(request, appointment_id):
    """
    SECURED: Cancel appointment with enhanced verification
    """
    patient, patient_dict = get_current_patient(request)
    if patient is None:
        raise Http404("Access denied")
    
    if request.method == 'POST':
        try:
            # CRITICAL: Enhanced ownership verification
            from common.models import Appointment
            appointment = get_object_or_404(
                Appointment.objects.select_related('patient'),
                id=appointment_id,
                patient=request.user,
                patient__patient_profile=patient
            )
            
            # ADDITIONAL SECURITY: Check appointment isn't already cancelled/completed
            if appointment.status in ['Cancelled', 'Completed']:
                logger.warning(f"SECURITY: User {request.user.username} attempted to cancel already {appointment.status.lower()} appointment {appointment_id}")
                messages.error(request, f"Cannot cancel {appointment.status.lower()} appointment.")
                return redirect('patient:patient_appointments')
            
            # BUSINESS RULE: Check cancellation timing (24-hour rule)
            from django.utils import timezone
            from datetime import timedelta
            
            if appointment.time <= timezone.now() + timedelta(hours=24):
                logger.warning(f"SECURITY: Late cancellation attempted by user {request.user.username} for appointment {appointment_id}")
                messages.warning(request, "Appointments should be cancelled at least 24 hours in advance. A late cancellation fee may apply.")
            
            # Cancel appointment
            appointment.status = 'Cancelled'
            appointment.save()
            
            # Log cancellation for audit
            logger.info(f"AUDIT: User {request.user.username} cancelled appointment {appointment_id}")
            messages.success(request, "Appointment cancelled successfully.")
            
        except Exception as e:
            logger.error(f"SECURITY: Appointment cancellation error for user {request.user.username}: {str(e)}")
            messages.error(request, "Error cancelling appointment.")
    
    return redirect('patient:patient_appointments')
