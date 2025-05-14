# patient/views/appointments.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from patient.decorators import patient_required
from common.models import Appointment
from provider.models import Provider
from patient.services.appointment_service import AppointmentService

# Uncomment for API-based implementation
# import requests
# import json
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def appointments_view(request):
    """Patient appointments view using database models"""
    patient = request.patient
    
    # Get appointments - use request.user instead of patient
    today = timezone.now()
    upcoming_appointments = Appointment.objects.filter(
        patient=request.user,  # Use request.user, not patient
        time__gte=today
    ).order_by('time')
    
    past_appointments = Appointment.objects.filter(
        patient=request.user,  # Use request.user, not patient
        time__lt=today
    ).order_by('-time')[:10]  # Last 10 past appointments
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'today': today,
        'active_section': 'appointments'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get upcoming appointments
    #     upcoming_response = requests.get(
    #         f"{api_url}appointments/upcoming/",
    #         headers=headers
    #     )
    #     upcoming_appointments = upcoming_response.json()['results'] if upcoming_response.ok else []
    #     
    #     # Get past appointments
    #     past_response = requests.get(
    #         f"{api_url}appointments/past/?limit=10",
    #         headers=headers
    #     )
    #     past_appointments = past_response.json()['results'] if past_response.ok else []
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'appointments': upcoming_appointments,
    #         'past_appointments': past_appointments,
    #         'today': today,
    #         'active_section': 'appointments'
    #     }
    # except Exception as e:
    #     # Handle API errors
    #     messages.error(request, f"Error loading appointments: {str(e)}")
    
    return render(request, "patient/appointments.html", context)

@patient_required
def schedule_appointment(request):
    """Schedule new appointment using database models"""
    patient = request.patient
    
    if request.method == 'POST':
        # Get form data
        provider_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        appointment_type = request.POST.get('appointment_type')
        reason = request.POST.get('reason')
        notes = request.POST.get('notes', '')
        
        # Use the service to schedule the appointment
        result = AppointmentService.schedule_appointment(
            patient=patient,
            doctor_id=provider_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            appointment_type=appointment_type,
            reason=reason,
            notes=notes
        )
        
        if isinstance(result, Appointment):
            messages.success(request, "Appointment scheduled successfully!")
            return redirect('patient:patient_appointments')
        else:
            messages.error(request, f"Error scheduling appointment: {result.get('error', 'Please try again.')}")
    
    # For GET requests, display the scheduling form
    available_providers = Provider.objects.filter(is_active=True)
    
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(14):  # Next two weeks
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'available_providers': available_providers,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # if request.method == 'POST':
    #     # Prepare API payload
    #     payload = {
    #         'doctor': request.POST.get('doctor'),
    #         'appointment_date': request.POST.get('appointment_date'),
    #         'appointment_time': request.POST.get('appointment_time'),
    #         'appointment_type': request.POST.get('appointment_type'),
    #         'reason': request.POST.get('reason'),
    #         'notes': request.POST.get('notes', '')
    #     }
    #     
    #     try:
    #         # Make API request to schedule appointment
    #         response = requests.post(
    #             f"{api_url}appointments/",
    #             headers=headers,
    #             json=payload
    #         )
    #         
    #         if response.ok:
    #             messages.success(request, "Appointment scheduled successfully!")
    #             return redirect('patient:patient_appointments')
    #         else:
    #             error_message = response.json().get('detail', 'Please try again.')
    #             messages.error(request, f"Error scheduling appointment: {error_message}")
    #     except Exception as e:
    #         messages.error(request, f"Error scheduling appointment: {str(e)}")
    # 
    # # For GET requests, get providers, dates, and times
    # try:
    #     # Get available providers
    #     providers_response = requests.get(
    #         f"{settings.API_BASE_URL}/api/providers/",
    #         headers=headers
    #     )
    #     available_providers = providers_response.json()['results'] if providers_response.ok else []
    #     
    #     # Get available slots
    #     slots_response = requests.get(
    #         f"{api_url}appointments/available-slots/",
    #         headers=headers
    #     )
    #     
    #     if slots_response.ok:
    #         slots_data = slots_response.json()
    #         available_dates = slots_data.get('dates', [])
    #         available_times = slots_data.get('times', [])
    #     else:
    #         # Fallback to default values
    #         available_dates = []
    #         start_date = timezone.now().date()
    #         for i in range(14):  # Next two weeks
    #             available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    #         
    #         available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'available_providers': available_providers,
    #         'available_dates': available_dates,
    #         'available_times': available_times,
    #         'active_section': 'appointments'
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading appointment form: {str(e)}")
    
    return render(request, "patient/schedule_appointment.html", context)

@patient_required
def reschedule_appointment(request, appointment_id):
    """View for patient to reschedule an existing appointment"""
    patient = request.patient
    
    # Get the appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id, patient=request.user)
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
        return redirect('patient:patient_appointments')
    
    if request.method == 'POST':
        # Extract new appointment time from form
        new_time_data = {
            'time': request.POST.get('appointment_date') + ' - ' + request.POST.get('appointment_time')
        }
        
        # Use the service to reschedule the appointment
        result = AppointmentService.reschedule_appointment(
            appointment_id=appointment_id,
            patient=patient,
            new_time_data=new_time_data
        )
        
        if result.get('success'):
            messages.success(request, "Appointment rescheduled successfully!")
            return redirect('patient:patient_appointments')
        else:
            messages.error(request, f"There was an error rescheduling your appointment: {result.get('error', 'Please try again.')}")
    
    # For GET requests, display the rescheduling form
    # Generate available time slots
    available_dates = []
    start_date = timezone.now().date()
    for i in range(14):  # Next two weeks
        available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    
    available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'appointment': appointment,
        'available_dates': available_dates,
        'available_times': available_times,
        'active_section': 'appointments'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get appointment details
    #     appointment_response = requests.get(
    #         f"{api_url}appointments/{appointment_id}/",
    #         headers=headers
    #     )
    #     
    #     if not appointment_response.ok:
    #         messages.error(request, "Appointment not found or you don't have permission to view it.")
    #         return redirect('patient:patient_appointments')
    #     
    #     appointment = appointment_response.json()
    #     
    #     if request.method == 'POST':
    #         # Prepare API payload
    #         payload = {
    #             'appointment_date': request.POST.get('appointment_date'),
    #             'appointment_time': request.POST.get('appointment_time')
    #         }
    #         
    #         # Make API request to reschedule appointment
    #         reschedule_response = requests.patch(
    #             f"{api_url}appointments/{appointment_id}/",
    #             headers=headers,
    #             json=payload
    #         )
    #         
    #         if reschedule_response.ok:
    #             messages.success(request, "Appointment rescheduled successfully!")
    #             return redirect('patient:patient_appointments')
    #         else:
    #             error_message = reschedule_response.json().get('detail', 'Please try again.')
    #             messages.error(request, f"There was an error rescheduling your appointment: {error_message}")
    #     
    #     # Get available slots
    #     slots_response = requests.get(
    #         f"{api_url}appointments/available-slots/",
    #         headers=headers
    #     )
    #     
    #     if slots_response.ok:
    #         slots_data = slots_response.json()
    #         available_dates = slots_data.get('dates', [])
    #         available_times = slots_data.get('times', [])
    #     else:
    #         # Fallback to default values
    #         available_dates = []
    #         start_date = timezone.now().date()
    #         for i in range(14):  # Next two weeks
    #             available_dates.append((start_date + timedelta(days=i)).strftime('%Y-%m-%d'))
    #         
    #         available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'appointment': appointment,
    #         'available_dates': available_dates,
    #         'available_times': available_times,
    #         'active_section': 'appointments'
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading appointment data: {str(e)}")
    #     return redirect('patient:patient_appointments')
    
    return render(request, "patient/reschedule_appointment.html", context)

@patient_required
def cancel_appointment(request, appointment_id):
    """View for patient to cancel an appointment"""
    patient = request.patient
    
    if request.method == 'POST':
        # Use the service to cancel the appointment
        result = AppointmentService.cancel_appointment(
            appointment_id=appointment_id,
            patient=patient
        )
        
        if result.get('success'):
            messages.success(request, "Appointment cancelled successfully.")
        else:
            messages.error(request, f"There was an error cancelling your appointment: {result.get('error', 'Please try again.')}")
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # if request.method == 'POST':
    #     try:
    #         # Make API request to cancel appointment
    #         cancel_response = requests.post(
    #             f"{api_url}appointments/{appointment_id}/cancel/",
    #             headers=headers
    #         )
    #         
    #         if cancel_response.ok:
    #             messages.success(request, "Appointment cancelled successfully.")
    #         else:
    #             error_message = cancel_response.json().get('detail', 'Please try again.')
    #             messages.error(request, f"There was an error cancelling your appointment: {error_message}")
    #     except Exception as e:
    #         messages.error(request, f"Error cancelling appointment: {str(e)}")
    
    return redirect('patient:patient_appointments')
