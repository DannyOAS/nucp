# provider/views/prescriptions.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, date
import logging

from provider.services import PrescriptionService
from provider.utils import get_current_provider
from api.v1.provider.serializers import PrescriptionSerializer

logger = logging.getLogger(__name__)

@login_required
def provider_prescriptions(request):
    """Provider prescriptions view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    time_period = request.GET.get('period', 'week')
    search_query = request.GET.get('search', '')
    
    try:
        # Get prescriptions data from service
        prescriptions_data = PrescriptionService.get_provider_prescriptions_dashboard(
            provider_id=provider.id,
            time_period=time_period,
            search_query=search_query
        )
        
        # Format recent prescriptions using API serializer if needed
        recent_prescriptions = prescriptions_data.get('recent_prescriptions', [])
        if hasattr(recent_prescriptions, 'model'):
            serializer = PrescriptionSerializer(recent_prescriptions, many=True)
            prescriptions_data['recent_prescriptions'] = serializer.data
        
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
        prescription_requests = prescriptions_data.get('prescription_requests', [])
        process_prescription_requests(prescription_requests)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'stats': prescriptions_data.get('stats', {}),
            'prescription_requests': prescription_requests,
            'recent_prescriptions': page_obj,
            'active_section': 'prescriptions',
            'time_period': time_period,
            'search_query': search_query,
            'page_obj': page_obj
        }
    except Exception as e:
        logger.error(f"Exception in service call: {e}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'stats': {
                'active_prescriptions': 0,
                'pending_renewals': 0,
                'new_today': 0,
                'refill_requests': 0
            },
            'prescription_requests': [],
            'recent_prescriptions': [],
            'active_section': 'prescriptions',
            'time_period': time_period,
            'search_query': search_query,
            'page_obj': None
        }
    
    return render(request, 'provider/prescriptions.html', context)

def process_prescription_requests(requests):
    """Process expiration dates for prescription requests"""
    today = datetime.now().date()
    for req in requests:
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

@login_required
def approve_prescription(request, prescription_id):
    """Approve a prescription request with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Approve prescription using service
        result = PrescriptionService.approve_prescription(
            prescription_id=prescription_id,
            provider_id=provider.id
        )
        
        if result.get('success', False):
            messages.success(request, "Prescription approved successfully.")
        else:
            messages.error(request, result.get('error', "Error approving prescription."))
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
        # Get prescription data using service
        prescription_data = PrescriptionService.get_prescription_details(
            prescription_id=prescription_id,
            provider_id=provider.id
        )
        
        if not prescription_data.get('success', False):
            messages.error(request, prescription_data.get('error', "Prescription not found."))
            return redirect('provider_prescriptions')
        
        # Format prescription data with serializer if needed
        prescription = prescription_data.get('prescription')
        if prescription and hasattr(prescription, '__dict__'):
            serializer = PrescriptionSerializer(prescription)
            prescription = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'prescription': prescription,
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error retrieving prescription: {str(e)}")
        messages.error(request, f"Error retrieving prescription: {str(e)}")
        return redirect('provider_prescriptions')
    
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
            # Create prescription using service
            prescription_data = {
                'patient_id': request.POST.get('patient_id'),
                'medication_name': request.POST.get('medication_name'),
                'dosage': request.POST.get('dosage'),
                'frequency': request.POST.get('frequency'),
                'duration': request.POST.get('duration'),
                'refills': request.POST.get('refills', 0),
                'instructions': request.POST.get('instructions'),
                'doctor_id': provider.id
            }
            
            result = PrescriptionService.create_prescription(prescription_data)
            
            if result.get('success', False):
                messages.success(request, "Prescription created successfully.")
                return redirect('provider_prescriptions')
            else:
                messages.error(request, result.get('error', "Error creating prescription."))
        except Exception as e:
            logger.error(f"Error creating prescription: {str(e)}")
            messages.error(request, f"Error creating prescription: {str(e)}")
    
    # For GET requests, prepare the form
    try:
        # Get form data from service
        form_data = PrescriptionService.get_prescription_form_data(provider.id)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': form_data.get('patients', []),
            'common_medications': form_data.get('common_medications', []),
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error retrieving form data: {str(e)}")
        # Default values if service fails
        common_medications = [
            'Amoxicillin', 'Lisinopril', 'Metformin', 'Atorvastatin', 
            'Levothyroxine', 'Amlodipine', 'Metoprolol', 'Omeprazole'
        ]
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'patients': [],
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
        # Get prescription data from service
        prescription_data = PrescriptionService.get_prescription_details(
            prescription_id=prescription_id,
            provider_id=provider.id
        )
        
        if not prescription_data.get('success', False):
            messages.error(request, prescription_data.get('error', "Prescription not found."))
            return redirect('provider_prescriptions')
        
        prescription = prescription_data.get('prescription')
        
        # Format prescription with serializer if needed
        if prescription and hasattr(prescription, '__dict__'):
            serializer = PrescriptionSerializer(prescription)
            prescription = serializer.data
    except Exception as e:
        logger.error(f"Error retrieving prescription: {str(e)}")
        messages.error(request, f"Error retrieving prescription: {str(e)}")
        return redirect('provider_prescriptions')
    
    if request.method == 'POST':
        try:
            # Update prescription using service
            updated_data = {
                'medication_name': request.POST.get('medication_name'),
                'dosage': request.POST.get('dosage'),
                'frequency': request.POST.get('frequency'),
                'duration': request.POST.get('duration'),
                'refills': request.POST.get('refills', 0),
                'instructions': request.POST.get('instructions'),
            }
            
            result = PrescriptionService.update_prescription(
                prescription_id=prescription_id,
                provider_id=provider.id,
                updated_data=updated_data
            )
            
            if result.get('success', False):
                messages.success(request, "Prescription updated successfully.")
                return redirect('provider_prescriptions')
            else:
                messages.error(request, result.get('error', "Error updating prescription."))
        except Exception as e:
            logger.error(f"Error updating prescription: {str(e)}")
            messages.error(request, f"Error updating prescription: {str(e)}")
    
    # For GET requests, prepare the form
    try:
        # Get form data from service
        form_data = PrescriptionService.get_prescription_form_data(provider.id)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'prescription': prescription,
            'common_medications': form_data.get('common_medications', []),
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error retrieving form data: {str(e)}")
        # Default values if service fails
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
