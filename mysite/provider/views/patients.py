from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from theme_name.repositories import ProviderRepository, PatientRepository, AppointmentRepository, PrescriptionRepository
from common.services import ProviderService
from theme_name.forms import PatientForm

def provider_patients(request):
    """Provider patients list view"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get search query if present
    search_query = request.GET.get('search', '')
    
    # Get filter parameter if present (all, recent, upcoming, attention)
    filter_type = request.GET.get('filter', 'all')
    
    # Get provider patients
    patients = ProviderRepository.get_patients(provider_id)
    
    # Apply search filter if search query exists
    if search_query:
        patients = [
            p for p in patients 
            if search_query.lower() in p.get('first_name', '').lower() or 
               search_query.lower() in p.get('last_name', '').lower() or
               search_query.lower() in p.get('email', '').lower() or
               search_query.lower() in p.get('ohip_number', '').lower()
        ]
    
    # Apply additional filters based on filter_type
    if filter_type == 'recent':
        # Filter patients with recent activity (last 7 days)
        # This is a simplification - in a real app you'd check last_visit dates
        patients = [p for p in patients if p.get('last_visit', '') != '']
    elif filter_type == 'upcoming':
        # Filter patients with upcoming appointments
        patients = [p for p in patients if p.get('upcoming_appointment', '') != '']
    elif filter_type == 'attention':
        # Filter patients requiring attention
        # This could be based on various criteria - here we're using a simplification
        patients = [p for p in patients if 'requires_attention' in p and p['requires_attention']]
    
    # Handle pagination
    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(patients, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get recent patient activity
    recent_activity = ProviderService.get_recent_patient_activity(provider_id)
    
    # Calculate stats
    total_patients = len(ProviderRepository.get_patients(provider_id))
    appointments_this_week = len([p for p in patients if p.get('upcoming_appointment', '') != ''])
    requiring_attention = len([p for p in patients if 'requires_attention' in p and p['requires_attention']])
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
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

def add_patient(request):
    """Add a new patient"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            # Save patient data
            result = ProviderService.add_patient(form.cleaned_data)
            
            # Check if the upload to cloud was successful
            if result.get('patient'):
                if result.get('cloud_upload', {}).get('success'):
                    messages.success(request, f"Patient {form.cleaned_data['first_name']} {form.cleaned_data['last_name']} was added successfully and documents were uploaded to cloud.")
                else:
                    messages.warning(request, f"Patient {form.cleaned_data['first_name']} {form.cleaned_data['last_name']} was added successfully, but there was an issue uploading to cloud.")
                
                return redirect('provider_patients')
            else:
                messages.error(request, "There was an error adding the patient.")
    else:
        form = PatientForm()
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'form': form,
        'active_section': 'patients'
    }
    return render(request, 'provider/add_patient.html', context)

def view_patient(request, patient_id):
    """View patient details"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get patient data
    patient = PatientRepository.get_by_id(patient_id)
    
    print(f"[VIEW] Retrieved patient: {patient.get('first_name')} {patient.get('last_name')}, ID: {patient.get('id')}")

    if not patient:
        messages.error(request, f"Patient with ID {patient_id} not found.")
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
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'patient': patient,
        'patient_name': patient_name,
        'appointments': appointments,
        'past_appointments': past_appointments,
        'prescriptions': prescriptions,
        'historical_prescriptions': historical_prescriptions,
        'active_section': 'patients'
    }
    
    return render(request, 'provider/view_patient.html', context)
