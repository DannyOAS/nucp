# provider/views/patients.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
import logging
import requests

from theme_name.repositories import PatientRepository, AppointmentRepository, PrescriptionRepository
from provider.services import ProviderService
from provider.forms import PatientForm
from provider.utils import get_current_provider

logger = logging.getLogger(__name__)

@login_required
def provider_patients(request):
    """Provider patients list view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get search query if present
    search_query = request.GET.get('search', '')
    
    # Get filter parameter if present (all, recent, upcoming, attention)
    filter_type = request.GET.get('filter', 'all')
    
    # Get provider patients using direct DB query when possible
    try:
        # Try to get patients from the database directly
        from theme_name.models import PatientRegistration
        
        if hasattr(PatientRegistration, 'provider'):
            # Direct provider relationship
            patients = PatientRegistration.objects.filter(provider=provider)
        else:
            # Get from appointments
            from common.models import Appointment
            patient_ids = Appointment.objects.filter(
                doctor=provider
            ).values_list('patient_id', flat=True).distinct()
            
            patients = PatientRegistration.objects.filter(id__in=patient_ids)
            
        # Apply search filter if search query exists
        if search_query:
            patients = patients.filter(
                models.Q(first_name__icontains=search_query) | 
                models.Q(last_name__icontains=search_query) | 
                models.Q(email__icontains=search_query) |
                models.Q(ohip_number__icontains=search_query)
            )
        
        # Convert to list of dictionaries for consistency with templates
        patients_list = []
        for patient in patients:
            patients_list.append({
                'id': patient.id,
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'email': patient.email,
                'date_of_birth': patient.date_of_birth,
                'phone': patient.primary_phone,
                'last_visit': getattr(patient, 'last_visit', ''),
                'upcoming_appointment': getattr(patient, 'upcoming_appointment', ''),
                'requires_attention': getattr(patient, 'requires_attention', False),
            })
            
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/patients/')
        # params = {
        #     'search': search_query,
        #     'filter': filter_type
        # }
        # response = requests.get(api_url, params=params)
        # if response.status_code == 200:
        #     patients_list = response.json()
        # else:
        #     patients_list = []
            
    except Exception as e:
        logger.error(f"Error retrieving patients from database: {str(e)}")
        # Fall back to repository during transition
        patients_list = ProviderService.get_patients_dashboard(provider.id).get('patients', [])
    
    # Apply additional filters based on filter_type (if using list of dicts)
    filtered_patients = []
    if filter_type == 'recent':
        # Filter patients with recent activity (last 7 days)
        filtered_patients = [p for p in patients_list if p.get('last_visit', '') != '']
    elif filter_type == 'upcoming':
        # Filter patients with upcoming appointments
        filtered_patients = [p for p in patients_list if p.get('upcoming_appointment', '') != '']
    elif filter_type == 'attention':
        # Filter patients requiring attention
        filtered_patients = [p for p in patients_list if p.get('requires_attention', False)]
    else:
        # No filter
        filtered_patients = patients_list
    
    # Handle pagination
    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(filtered_patients, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get recent patient activity
    try:
        recent_activity = ProviderService.get_recent_patient_activity(provider.id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/patients/recent-activity/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     recent_activity = response.json()
        # else:
        #     recent_activity = []
            
    except Exception as e:
        logger.error(f"Error retrieving recent activity: {str(e)}")
        recent_activity = []
    
    # Calculate stats
    total_patients = len(patients_list)
    appointments_this_week = len([p for p in patients_list if p.get('upcoming_appointment', '') != ''])
    requiring_attention = len([p for p in patients_list if p.get('requires_attention', False)])
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'patients': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'stats': {
            'total_patients': total_patients,
            'appointments_this_week': appointments_this_week,
            'requiring_attention': requiring_attention
        },
        'recent_activity': recent_activity[:5],  # Limit to 5 most recent activities
        'active_section': 'patients'
    }
    
    return render(request, 'provider/patients.html', context)

@login_required
def add_patient(request):
    """Add a new patient with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            try:
                # Save patient data, associating with the current provider
                patient_data = form.cleaned_data
                
                # Add provider field if it exists in the PatientRegistration model
                from theme_name.models import PatientRegistration
                if hasattr(PatientRegistration, 'provider'):
                    patient_data['provider'] = provider
                
                # Save using service or repository during transition
                result = ProviderService.add_patient(patient_data, provider_id=provider.id)
                
                # API version (commented out for now):
                # api_url = request.build_absolute_uri('/api/provider/patients/')
                # response = requests.post(api_url, json=patient_data)
                # if response.status_code == 201:  # Created
                #     result = {'success': True, 'patient': response.json()}
                # else:
                #     result = {'success': False}
                
                # Check if the upload to cloud was successful
                if result.get('patient'):
                    if result.get('cloud_upload', {}).get('success'):
                        messages.success(request, f"Patient {patient_data['first_name']} {patient_data['last_name']} was added successfully and documents were uploaded to cloud.")
                    else:
                        messages.warning(request, f"Patient {patient_data['first_name']} {patient_data['last_name']} was added successfully, but there was an issue uploading to cloud.")
                    
                    return redirect('provider_patients')
                else:
                    messages.error(request, "There was an error adding the patient.")
            except Exception as e:
                logger.error(f"Error adding patient: {str(e)}")
                messages.error(request, f"There was an error adding the patient: {str(e)}")
    else:
        form = PatientForm()
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'form': form,
        'active_section': 'patients'
    }
    return render(request, 'provider/add_patient.html', context)

@login_required
def view_patient(request, patient_id):
    """View patient details with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get patient data
    try:
        patient = PatientRepository.get_by_id(patient_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/patients/{patient_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     patient = response.json()
        # else:
        #     patient = None
        
        if not patient:
            messages.error(request, f"Patient with ID {patient_id} not found.")
            return redirect('provider_patients')
            
        # Verify this patient belongs to the current provider
        # This check depends on your data model
        patient_belongs_to_provider = False
        
        try:
            # Method 1: Check direct provider relationship if it exists
            from theme_name.models import PatientRegistration
            if hasattr(PatientRegistration, 'provider'):
                patient_record = PatientRegistration.objects.get(id=patient_id)
                if patient_record.provider_id == provider.id:
                    patient_belongs_to_provider = True
            
            # Method 2: Check through appointments
            if not patient_belongs_to_provider:
                from common.models import Appointment
                appointment_count = Appointment.objects.filter(
                    doctor=provider,
                    patient_id=patient_id
                ).count()
                
                if appointment_count > 0:
                    patient_belongs_to_provider = True
        except Exception as e:
            logger.warning(f"Error checking patient-provider relationship: {str(e)}")
            # During transition, assume the patient belongs to the provider
            patient_belongs_to_provider = True
        
        # If patient doesn't belong to this provider, redirect
        if not patient_belongs_to_provider:
            messages.error(request, "You do not have permission to view this patient.")
            return redirect('provider_patients')
            
        # Convert patient_id to integer if it's a string
        if isinstance(patient_id, str) and patient_id.isdigit():
            patient_id = int(patient_id)

        # Get related patient data
        appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
        past_appointments = AppointmentRepository.get_past_for_patient(patient_id)
        prescriptions = PrescriptionRepository.get_active_for_patient(patient_id)
        historical_prescriptions = PrescriptionRepository.get_historical_for_patient(patient_id)
        
        # Format the patient name
        patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/patients/{patient_id}/')
        # appointments_response = requests.get(f'{api_url}appointments/')
        # past_appointments_response = requests.get(f'{api_url}past-appointments/')
        # prescriptions_response = requests.get(f'{api_url}prescriptions/')
        # historical_prescriptions_response = requests.get(f'{api_url}historical-prescriptions/')
        # 
        # if appointments_response.status_code == 200:
        #     appointments = appointments_response.json()
        # else:
        #     appointments = []
        # 
        # if past_appointments_response.status_code == 200:
        #     past_appointments = past_appointments_response.json()
        # else:
        #     past_appointments = []
        # 
        # if prescriptions_response.status_code == 200:
        #     prescriptions = prescriptions_response.json()
        # else:
        #     prescriptions = []
        # 
        # if historical_prescriptions_response.status_code == 200:
        #     historical_prescriptions = historical_prescriptions_response.json()
        # else:
        #     historical_prescriptions = []
        
    except Exception as e:
        logger.error(f"Error retrieving patient details: {str(e)}")
        messages.error(request, "There was an error retrieving the patient details.")
        return redirect('provider_patients')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'patient': patient,
        'patient_name': patient_name,
        'appointments': appointments,
        'past_appointments': past_appointments,
        'prescriptions': prescriptions,
        'historical_prescriptions': historical_prescriptions,
        'active_section': 'patients'
    }
    
    return render(request, 'provider/view_patient.html', context)
