# provider/views/patients.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

from provider.services import PatientService
from provider.utils import get_current_provider
from provider.forms import PatientForm
from api.v1.patient.serializers import PatientSerializer

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
    
    try:
        # Get patients data from service
        patients_data = PatientService.get_provider_patients_dashboard(
            provider_id=provider.id,
            search_query=search_query,
            filter_type=filter_type
        )
        
        # Format patients list using API serializer if needed
        patients_list = patients_data.get('patients', [])
        if hasattr(patients_list, 'model'):
            serializer = PatientSerializer(patients_list, many=True)
            patients_list = serializer.data
        
        # Apply additional filters if necessary
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
        
        # Get patient activity
        recent_activity = patients_data.get('recent_activity', [])
        
        # Get stats
        stats = patients_data.get('stats', {
            'total_patients': len(patients_list),
            'appointments_this_week': 0,
            'requiring_attention': 0
        })
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
            'filter_type': filter_type,
            'stats': stats,
            'recent_activity': recent_activity[:5],  # Limit to 5 most recent activities
            'active_section': 'patients'
        }
    except Exception as e:
        logger.error(f"Error retrieving patients: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': [],
            'page_obj': None,
            'search_query': search_query,
            'filter_type': filter_type,
            'stats': {
                'total_patients': 0,
                'appointments_this_week': 0,
                'requiring_attention': 0
            },
            'recent_activity': [],
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
                # Add patient using service
                result = PatientService.add_patient(
                    patient_data=form.cleaned_data,
                    provider_id=provider.id
                )
                
                if result.get('success', False):
                    patient_data = form.cleaned_data
                    success_message = f"Patient {patient_data['first_name']} {patient_data['last_name']} was added successfully"
                    
                    # Check if documents were uploaded to cloud
                    if result.get('cloud_upload', {}).get('success'):
                        success_message += " and documents were uploaded to cloud."
                    else:
                        success_message += ", but there was an issue uploading to cloud."
                    
                    messages.success(request, success_message)
                    return redirect('provider_patients')
                else:
                    messages.error(request, result.get('error', "There was an error adding the patient."))
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
    
    try:
        # Get patient data from service
        patient_data = PatientService.get_patient_details(
            patient_id=patient_id,
            provider_id=provider.id
        )
        
        if not patient_data.get('success', False):
            messages.error(request, patient_data.get('error', f"Patient with ID {patient_id} not found."))
            return redirect('provider_patients')
        
        # Get related data
        patient = patient_data.get('patient', {})
        appointments = patient_data.get('appointments', [])
        past_appointments = patient_data.get('past_appointments', [])
        prescriptions = patient_data.get('prescriptions', [])
        historical_prescriptions = patient_data.get('historical_prescriptions', [])
        
        # Format patient name
        patient_name = patient_data.get('patient_name', f"{patient.get('first_name', '')} {patient.get('last_name', '')}")
        
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
    except Exception as e:
        logger.error(f"Error retrieving patient details: {str(e)}")
        messages.error(request, "There was an error retrieving the patient details.")
        return redirect('provider_patients')
    
    return render(request, 'provider/view_patient.html', context)
