# provider/views/appointments.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from provider.services.appointment_service import AppointmentService
from provider.utils import get_current_provider
from api.v1.provider.serializers import AppointmentSerializer

logger = logging.getLogger(__name__)

@login_required
def provider_appointments(request):
    """Provider appointments view with calendar integration"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Handle view type selection
    view_type = request.GET.get('view', 'week')  # Default to week view
    
    # Handle date navigation
    selected_date_str = request.GET.get('date')
    
    try:
        # Get appointments data from service
        appointments_data = AppointmentService.get_provider_calendar_view(
            provider_id=provider.id,
            selected_date=selected_date_str,
            view_type=view_type
        )
        
        # Format appointments using API serializer if needed
        appointments = appointments_data.get('appointments', [])
        if hasattr(appointments, 'model'):
            serializer = AppointmentSerializer(appointments, many=True)
            appointments_data['appointments'] = serializer.data
        
        todays_appointments = appointments_data.get('todays_appointments', [])
        if hasattr(todays_appointments, 'model'):
            serializer = AppointmentSerializer(todays_appointments, many=True)
            appointments_data['todays_appointments'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'appointments': appointments_data.get('appointments', []),
            'todays_appointments': appointments_data.get('todays_appointments', []),
            'calendar_data': appointments_data.get('calendar_data', {}),
            'view_type': view_type,
            'selected_date': appointments_data.get('selected_date', timezone.now().date()),
            'date_display': appointments_data.get('date_display', ''),
            'prev_date': appointments_data.get('prev_date', ''),
            'next_date': appointments_data.get('next_date', ''),
            'today_date': timezone.now().date().strftime('%Y-%m-%d'),
            'stats': appointments_data.get('stats', {
                'today_count': 0,
                'upcoming_count': 0,
                'completed_count': 0,
                'cancelled_count': 0
            }),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error retrieving appointments: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'appointments': [],
            'todays_appointments': [],
            'calendar_data': {},
            'view_type': view_type,
            'selected_date': timezone.now().date(),
            'date_display': timezone.now().date().strftime('%B %d, %Y'),
            'prev_date': (timezone.now().date() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'next_date': (timezone.now().date() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'today_date': timezone.now().date().strftime('%Y-%m-%d'),
            'stats': {
                'today_count': 0,
                'upcoming_count': 0,
                'completed_count': 0,
                'cancelled_count': 0
            },
            'active_section': 'appointments'
        }
    
    return render(request, "provider/appointments.html", context)

@login_required
def view_appointment(request, appointment_id):
    """View for provider to see appointment details"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get appointment details from service
        appointment_data = AppointmentService.get_appointment_details(
            appointment_id=appointment_id,
            provider_id=provider.id
        )
        
        if not appointment_data.get('success', False):
            messages.error(request, appointment_data.get('error', "Appointment not found."))
            return redirect('provider_appointments')
        
        # Format appointment data using serializer if needed
        appointment = appointment_data.get('appointment')
        if appointment and hasattr(appointment, '__dict__'):
            serializer = AppointmentSerializer(appointment)
            appointment = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'appointment': appointment,
            'patient': appointment_data.get('patient'),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error retrieving appointment details: {str(e)}")
        messages.error(request, "There was an error retrieving the appointment details.")
        return redirect('provider_appointments')
    
    return render(request, "provider/view_appointment.html", context)

@login_required
def schedule_appointment(request):
    """View for provider to schedule a new appointment"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Create appointment using service
            result = AppointmentService.create_appointment(
                provider_id=provider.id,
                form_data=request.POST
            )
            
            if result.get('success', False):
                messages.success(request, "Appointment scheduled successfully!")
                return redirect('provider_appointments')
            else:
                messages.error(request, result.get('error', "Error scheduling appointment."))
        except Exception as e:
            logger.error(f"Error scheduling appointment: {str(e)}")
            messages.error(request, f"Error scheduling appointment: {str(e)}")
    
    # For GET requests, prepare the scheduling form
    try:
        # Get form data from service
        form_data = AppointmentService.get_scheduling_form_data(provider.id)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': form_data.get('patients', []),
            'available_dates': form_data.get('available_dates', []),
            'available_times': form_data.get('available_times', []),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error loading scheduling form: {str(e)}")
        # Fallback data
        start_date = timezone.now().date()
        available_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': [],
            'available_dates': available_dates,
            'available_times': available_times,
            'active_section': 'appointments'
        }
    
    return render(request, "provider/schedule_appointment.html", context)

@login_required
def reschedule_appointment(request, appointment_id):
    """View for provider to reschedule an existing appointment"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get appointment for rescheduling
        appointment_data = AppointmentService.get_appointment_for_reschedule(
            appointment_id=appointment_id,
            provider_id=provider.id
        )
        
        if not appointment_data.get('success', False):
            messages.error(request, appointment_data.get('error', "Appointment not found."))
            return redirect('provider_appointments')
            
        appointment = appointment_data.get('appointment')
        
        # Format appointment using serializer if needed
        if appointment and hasattr(appointment, '__dict__'):
            serializer = AppointmentSerializer(appointment)
            appointment = serializer.data
        
        if request.method == 'POST':
            # Process reschedule using service
            result = AppointmentService.reschedule_appointment(
                appointment_id=appointment_id,
                provider_id=provider.id,
                form_data=request.POST,
                provider_initiated=True
            )
            
            if result.get('success', False):
                messages.success(request, "Appointment rescheduled successfully!")
                return redirect('provider_appointments')
            else:
                messages.error(request, result.get('error', "Error rescheduling appointment."))
    except Exception as e:
        logger.error(f"Error loading appointment for reschedule: {str(e)}")
        messages.error(request, f"Error loading appointment: {str(e)}")
        return redirect('provider_appointments')
    
    # For GET requests, prepare the rescheduling form
    try:
        # Get form data from service
        form_data = AppointmentService.get_scheduling_form_data(provider.id)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'appointment': appointment,
            'available_dates': form_data.get('available_dates', []),
            'available_times': form_data.get('available_times', []),
            'active_section': 'appointments'
        }
    except Exception as e:
        logger.error(f"Error loading rescheduling form: {str(e)}")
        # Fallback data
        start_date = timezone.now().date()
        available_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        available_times = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM']
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'appointment': appointment,
            'available_dates': available_dates,
            'available_times': available_times,
            'active_section': 'appointments'
        }
    
    return render(request, "provider/reschedule_appointment.html", context)

@login_required
def update_appointment_status(request, appointment_id):
    """View for provider to update appointment status"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        
        if status not in ['Scheduled', 'Checked In', 'In Progress', 'Completed', 'Cancelled', 'No Show']:
            messages.error(request, "Invalid appointment status.")
            return redirect('provider_appointments')
        
        try:
            # Update status using service
            result = AppointmentService.update_appointment_status(
                appointment_id=appointment_id,
                provider_id=provider.id,
                status=status
            )
            
            if result.get('success', False):
                messages.success(request, f"Appointment status updated to {status}.")
                
                # If appointment was cancelled, handle additional logic
                if status == 'Cancelled' and not result.get('calendar_sync', {}).get('success', True):
                    messages.warning(request, "Appointment status was updated, but there was an issue syncing with the calendar.")
            else:
                messages.error(request, result.get('error', "Error updating appointment status."))
        except Exception as e:
            logger.error(f"Error updating appointment status: {str(e)}")
            messages.error(request, f"Error updating appointment status: {str(e)}")
    
    return redirect('provider_appointments')

@login_required
def get_appointment_date(request):
    """Helper function to get appointment date from request parameters"""
    try:
        date_str = request.GET.get('date')
        if date_str:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        return timezone.now().date()
    except ValueError:
        return timezone.now().date()

@login_required
def process_appointments_for_calendar(appointments, start_date, end_date, view_type):
    """Process appointments for calendar display"""
    return AppointmentService.process_appointments_for_calendar(
        appointments, start_date, end_date, view_type
    )
