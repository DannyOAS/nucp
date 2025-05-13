# provider/views/prescriptions.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
import requests
from datetime import datetime, date

from theme_name.repositories import PrescriptionRepository
from provider.services import ProviderService, PrescriptionService
from provider.utils import get_current_provider
from theme_name.data_access import get_provider_prescription_requests

logger = logging.getLogger(__name__)

@login_required
def provider_prescriptions(request):
    """Provider prescriptions view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Direct data access test (for debugging)
    direct_data = get_provider_prescription_requests(provider.id)
    logger.debug(f"Direct data access call result: {direct_data}")

    time_period = request.GET.get('period', 'week')
    search_query = request.GET.get('search', '')
    
    try:
        # Use service layer for now, but could switch to API
        prescriptions_data = ProviderService.get_prescriptions_dashboard(
            provider.id,  # Use authenticated provider ID
            time_period=time_period,
            search_query=search_query
        )
        logger.debug("Service call successful")
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/')
        # params = {
        #     'time_period': time_period,
        #     'search': search_query
        # }
        # response = requests.get(f'{api_url}prescriptions/', params=params)
        # if response.status_code == 200:
        #     prescriptions_data = response.json()
        # else:
        #     prescriptions_data = {
        #         'stats': {'active_prescriptions': 0, 'pending_renewals': 0, 'new_today': 0, 'refill_requests': 0},
        #         'prescription_requests': [],
        #         'recent_prescriptions': []
        #     }
        
    except Exception as e:
        logger.error(f"Exception in service call: {e}")
        prescriptions_data = {
            'stats': {'active_prescriptions': 0, 'pending_renewals': 0, 'new_today': 0, 'refill_requests': 0},
            'prescription_requests': [],
            'recent_prescriptions': []
        }
    
    logger.debug(f"Full prescriptions_data: {prescriptions_data}")

    # Pagination
    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(prescriptions_data.get('recent_prescriptions', []), items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Process expiration dates for prescription requests
    today = datetime.now().date()
    for req in prescriptions_data.get('prescription_requests', []):
        req['expiration_date'] = req.get('expires', 'N/A')
        req['days_left'] = None
        
        if 'expires' in req:
            try:
                expiration_date = None
                if isinstance(req['expires'], str):
                    formats = ['%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']
                    for fmt in formats:
                        try:
                            expiration_date = datetime.strptime(req['expires'], fmt).date()
                            break
                        except ValueError:
                            continue
                elif isinstance(req['expires'], datetime):
                    expiration_date = req['expires'].date()
                elif isinstance(req['expires'], date):
                    expiration_date = req['expires']
                
                if expiration_date:
                    req['days_left'] = max(0, (expiration_date - today).days)
            except Exception as e:
                logger.warning(f"Error calculating expiration for {req.get('medication_name')}: {e}")

    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'stats': prescriptions_data.get('stats', {}),
        'prescription_requests': prescriptions_data.get('prescription_requests', []),
        'recent_prescriptions': page_obj,
        'active_section': 'prescriptions',
        'time_period': time_period,
        'search_query': search_query,
        'page_obj': page_obj
    }
    
    return render(request, 'provider/prescriptions.html', context)

@login_required
def approve_prescription(request, prescription_id):
    """Approve a prescription request with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Verify this prescription belongs to the current provider
        prescription = PrescriptionRepository.get_by_id(prescription_id)
        
        if not prescription or prescription.get('doctor_id') != provider.id:
            messages.error(request, "You do not have permission to approve this prescription.")
            return redirect('provider_prescriptions')
        
        # Approve the prescription
        result = PrescriptionService.approve_prescription(prescription_id, provider.id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/prescriptions/{prescription_id}/approve/')
        # response = requests.post(api_url)
        # if response.status_code == 200:
        #     result = response.json()
        # else:
        #     result = None
        
        if result:
            messages.success(request, "Prescription approved successfully.")
        else:
            messages.error(request, "Error approving prescription.")
    except Exception as e:
        logger.error(f"Error approving prescription: {str(e)}")
        messages.error(request, f"Error approving prescription: {str(e)}")
    
    return redirect('provider_prescriptions')

@login_required
def review_prescription(request, prescription_id):
    """Review a prescription request with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get prescription data
        prescription = PrescriptionRepository.get_by_id(prescription_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/prescriptions/{prescription_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     prescription = response.json()
        # else:
        #     prescription = None
        
        if not prescription:
            messages.error(request, "Prescription not found.")
            return redirect('provider_prescriptions')
        
        # Verify this prescription belongs to the current provider
        if prescription.get('doctor_id') != provider.id:
            messages.error(request, "You do not have permission to review this prescription.")
            return redirect('provider_prescriptions')
    except Exception as e:
        logger.error(f"Error retrieving prescription: {str(e)}")
        messages.error(request, f"Error retrieving prescription: {str(e)}")
        return redirect('provider_prescriptions')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/review_prescription.html', context)

@login_required
def create_prescription(request):
    """Create a new prescription with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process form data
            prescription_data = {
                'patient_id': request.POST.get('patient_id'),
                'medication_name': request.POST.get('medication_name'),
                'dosage': request.POST.get('dosage'),
                'frequency': request.POST.get('frequency'),
                'duration': request.POST.get('duration'),
                'refills': request.POST.get('refills', 0),
                'instructions': request.POST.get('instructions'),
                'doctor_id': provider.id,  # Use authenticated provider
            }
            
            # Create prescription
            result = PrescriptionService.create_prescription(prescription_data)
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri('/api/provider/prescriptions/')
            # response = requests.post(api_url, json=prescription_data)
            # if response.status_code == 201:  # Created
            #     result = {'success': True, 'prescription': response.json()}
            # else:
            #     result = {'success': False}
            
            if result and result.get('prescription'):
                messages.success(request, "Prescription created successfully.")
                return redirect('provider_prescriptions')
            else:
                messages.error(request, "Error creating prescription.")
        except Exception as e:
            logger.error(f"Error creating prescription: {str(e)}")
            messages.error(request, f"Error creating prescription: {str(e)}")
    
    # For GET requests, prepare the form
    try:
        # Get patients for this provider
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
            
        # Convert to list for template
        patients_list = []
        for patient in patients:
            patients_list.append({
                'id': patient.id,
                'name': f"{patient.first_name} {patient.last_name}"
            })
    except Exception as e:
        logger.error(f"Error retrieving patients: {str(e)}")
        patients_list = []
    
    # Get common medications (example data)
    common_medications = [
        'Amoxicillin', 'Lisinopril', 'Metformin', 'Atorvastatin', 
        'Levothyroxine', 'Amlodipine', 'Metoprolol', 'Omeprazole'
    ]
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'patients': patients_list,
        'common_medications': common_medications,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/create_prescription.html', context)

@login_required
def edit_prescription(request, prescription_id):
    """Edit an existing prescription with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get prescription data
        prescription = PrescriptionRepository.get_by_id(prescription_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/prescriptions/{prescription_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     prescription = response.json()
        # else:
        #     prescription = None
        
        if not prescription:
            messages.error(request, "Prescription not found.")
            return redirect('provider_prescriptions')
        
        # Verify this prescription belongs to the current provider
        if prescription.get('doctor_id') != provider.id:
            messages.error(request, "You do not have permission to edit this prescription.")
            return redirect('provider_prescriptions')
    except Exception as e:
        logger.error(f"Error retrieving prescription: {str(e)}")
        messages.error(request, f"Error retrieving prescription: {str(e)}")
        return redirect('provider_prescriptions')
    
    if request.method == 'POST':
        try:
            # Process form data
            updated_data = {
                'medication_name': request.POST.get('medication_name'),
                'dosage': request.POST.get('dosage'),
                'frequency': request.POST.get('frequency'),
                'duration': request.POST.get('duration'),
                'refills': request.POST.get('refills', 0),
                'instructions': request.POST.get('instructions'),
            }
            
            # Update prescription
            updated_prescription = PrescriptionRepository.update(prescription_id, updated_data)
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/provider/prescriptions/{prescription_id}/')
            # response = requests.patch(api_url, json=updated_data)
            # if response.status_code == 200:
            #     updated_prescription = response.json()
            # else:
            #     updated_prescription = None
            
            if updated_prescription:
                messages.success(request, "Prescription updated successfully.")
                return redirect('provider_prescriptions')
            else:
                messages.error(request, "Error updating prescription.")
        except Exception as e:
            logger.error(f"Error updating prescription: {str(e)}")
            messages.error(request, f"Error updating prescription: {str(e)}")
    
    # Get common medications (example data)
    common_medications = [
        'Amoxicillin', 'Lisinopril', 'Metformin', 'Atorvastatin', 
        'Levothyroxine', 'Amlodipine', 'Metoprolol', 'Omeprazole'
    ]
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'prescription': prescription,
        'common_medications': common_medications,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/edit_prescription.html', context)
