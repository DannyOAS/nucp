from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from datetime import datetime, date
from ...repositories import ProviderRepository, PrescriptionRepository
from ...services import ProviderService, PrescriptionService

logger = logging.getLogger(__name__)

def provider_prescriptions(request):
    """Provider prescriptions view"""
    provider_id = 1  # In production, get from request.user
    
    # Direct data access test (for debugging)
    from ...data_access import get_provider_prescription_requests
    direct_data = get_provider_prescription_requests(provider_id)
    print("DEBUG - Direct data access call result:", direct_data)

    time_period = request.GET.get('period', 'week')
    search_query = request.GET.get('search', '')
    try:
        prescriptions_data = ProviderService.get_prescriptions_dashboard(
            provider_id,
            time_period=time_period,
            search_query=search_query
        )
        print("DEBUG - Service call successful")
    except Exception as e:
        print(f"DEBUG - Exception in service call: {e}")
        prescriptions_data = {
            'stats': {'active_prescriptions': 0, 'pending_renewals': 0, 'new_today': 0, 'refill_requests': 0},
            'prescription_requests': [],
            'recent_prescriptions': []
        }
    print("DEBUG - Full prescriptions_data:", prescriptions_data)

    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(prescriptions_data.get('recent_prescriptions', []), items_per_page)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

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
        'stats': prescriptions_data.get('stats', {}),
        'prescription_requests': prescriptions_data.get('prescription_requests', []),
        'recent_prescriptions': page_obj,
        'active_section': 'prescriptions',
        'provider_name': 'Dr. Smith',
        'time_period': time_period,
        'search_query': search_query,
        'page_obj': page_obj
    }
    return render(request, 'provider/prescriptions.html', context)

def approve_prescription(request, prescription_id):
    """Approve a prescription request"""
    provider_id = 1  # In production, get from request.user
    
    result = PrescriptionService.approve_prescription(prescription_id, provider_id)
    
    if result:
        messages.success(request, "Prescription approved successfully.")
    else:
        messages.error(request, "Error approving prescription.")
    
    return redirect('provider_prescriptions')

def review_prescription(request, prescription_id):
    """Review a prescription request"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get prescription data
    prescription = PrescriptionRepository.get_by_id(prescription_id)
    
    if not prescription:
        messages.error(request, "Prescription not found.")
        return redirect('provider_prescriptions')
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/review_prescription.html', context)

def create_prescription(request):
    """Create a new prescription"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Placeholder - would use a form in the real implementation
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/create_prescription.html', context)

def edit_prescription(request, prescription_id):
    """Edit an existing prescription"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get prescription data
    prescription = PrescriptionRepository.get_by_id(prescription_id)
    
    if not prescription:
        messages.error(request, "Prescription not found.")
        return redirect('provider_prescriptions')
    
    # Placeholder - would use a form in the real implementation
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/edit_prescription.html', context)
