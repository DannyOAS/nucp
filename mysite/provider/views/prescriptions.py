from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
# from django.contrib.auth.decorators import login_required
import logging
from datetime import datetime, timedelta, date

from common.models import Prescription
from theme_name.models import PatientRegistration
from provider.models import Provider
from .dashboard import get_provider

logger = logging.getLogger(__name__)

# @login_required
def provider_prescriptions(request):
    """Provider prescriptions view using Django ORM"""
    provider = get_provider(request)
    
    # Get filter parameters
    time_period = request.GET.get('period', 'week')
    search_query = request.GET.get('search', '')
    
    # Define date ranges based on time period
    today = datetime.now().date()
    
    if time_period == 'today':
        start_date = today
    elif time_period == 'week':
        start_date = today - timedelta(days=7)
    elif time_period == 'month':
        start_date = today - timedelta(days=30)
    else:
        start_date = today - timedelta(days=7)
        time_period = 'week'
    
    # Query for prescription requests (pending renewals)
    prescription_requests = Prescription.objects.filter(
        doctor=provider,
        status='Pending'
    ).order_by('-created_at')
    
    # Query for recent prescriptions
    recent_prescriptions_query = Prescription.objects.filter(
        doctor=provider,
        created_at__date__gte=start_date
    ).order_by('-created_at')
    
    # Apply search filter if provided
    if search_query:
        recent_prescriptions_query = recent_prescriptions_query.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(medication_name__icontains=search_query)
        )
        
        prescription_requests = prescription_requests.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(medication_name__icontains=search_query)
        )
    
    # Handle pagination
    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(recent_prescriptions_query, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Calculate expiration dates and days left
    for req in prescription_requests:
        req.expiration_date = req.expires
        req.days_left = None
        
        if hasattr(req, 'expires') and req.expires:
            try:
                expiration_date = None
                if isinstance(req.expires, str):
                    formats = ['%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']
                    for fmt in formats:
                        try:
                            expiration_date = datetime.strptime(req.expires, fmt).date()
                            break
                        except ValueError:
                            continue
                elif isinstance(req.expires, datetime):
                    expiration_date = req.expires.date()
                elif isinstance(req.expires, date):
                    expiration_date = req.expires
                    
                if expiration_date:
                    req.days_left = max(0, (expiration_date - today).days)
            except Exception as e:
                logger.warning(f"Error calculating expiration for {req.medication_name}: {e}")
    
    # Calculate stats
    active_prescriptions = Prescription.objects.filter(
        doctor=provider,
        status='Active'
    ).count()
    
    pending_renewals = prescription_requests.count()
    
    new_today = Prescription.objects.filter(
        doctor=provider,
        created_at__date=today
    ).count()
    
    refill_requests = Prescription.objects.filter(
        doctor=provider,
        status='Pending',
        refill_requested=True
    ).count()
    
    context = {
        'stats': {
            'active_prescriptions': active_prescriptions,
            'pending_renewals': pending_renewals,
            'new_today': new_today,
            'refill_requests': refill_requests
        },
        'prescription_requests': prescription_requests,
        'recent_prescriptions': page_obj,
        'active_section': 'prescriptions',
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'time_period': time_period,
        'search_query': search_query,
        'page_obj': page_obj
    }
    
    return render(request, 'provider/prescriptions.html', context)

# @login_required
def approve_prescription(request, prescription_id):
    """Approve a prescription request"""
    provider = get_provider(request)
    
    # Get the prescription
    prescription = get_object_or_404(Prescription, id=prescription_id, doctor=provider)
    
    # Update prescription status
    prescription.status = 'Active'
    prescription.approved_date = timezone.now()
    prescription.save()
    
    messages.success(request, "Prescription approved successfully.")
    return redirect('provider_prescriptions')

# @login_required
def review_prescription(request, prescription_id):
    """Review a prescription request"""
    provider = get_provider(request)
    
    # Get prescription data
    prescription = get_object_or_404(Prescription, id=prescription_id, doctor=provider)
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/review_prescription.html', context)

# @login_required
def create_prescription(request):
    """Create a new prescription"""
    provider = get_provider(request)
    
    if request.method == 'POST':
        # Get form data
        patient_id = request.POST.get('patient')
        medication_name = request.POST.get('medication_name')
        dosage = request.POST.get('dosage')
        frequency = request.POST.get('frequency')
        duration = request.POST.get('duration')
        refills = request.POST.get('refills', 0)
        instructions = request.POST.get('instructions')
        
        # Validate required fields
        if not (patient_id and medication_name and dosage and frequency):
            messages.error(request, "Please fill in all required fields.")
            return redirect('create_prescription')
        
        try:
            # Get patient
            patient = PatientRegistration.objects.get(id=patient_id)
            
            # Create new prescription
            prescription = Prescription(
                patient=patient,
                doctor=provider,
                medication_name=medication_name,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                refills=refills,
                instructions=instructions,
                status='Active',
                created_at=timezone.now()
            )
            prescription.save()
            
            messages.success(request, "Prescription created successfully.")
            return redirect('provider_prescriptions')
            
        except PatientRegistration.DoesNotExist:
            messages.error(request, "Selected patient does not exist.")
        except Exception as e:
            logger.error(f"Error creating prescription: {e}")
            messages.error(request, "An error occurred while creating the prescription.")
    
    # Get patients for this provider
    patients = provider.get_patients()
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'patients': patients,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/create_prescription.html', context)

# @login_required
def edit_prescription(request, prescription_id):
    """Edit an existing prescription"""
    provider = get_provider(request)
    
    # Get prescription data
    prescription = get_object_or_404(Prescription, id=prescription_id, doctor=provider)
    
    if request.method == 'POST':
        # Get form data
        medication_name = request.POST.get('medication_name')
        dosage = request.POST.get('dosage')
        frequency = request.POST.get('frequency')
        duration = request.POST.get('duration')
        refills = request.POST.get('refills', 0)
        instructions = request.POST.get('instructions')
        status = request.POST.get('status')
        
        # Validate required fields
        if not (medication_name and dosage and frequency):
            messages.error(request, "Please fill in all required fields.")
        else:
            # Update prescription
            prescription.medication_name = medication_name
            prescription.dosage = dosage
            prescription.frequency = frequency
            prescription.duration = duration
            prescription.refills = refills
            prescription.instructions = instructions
            
            if status:
                prescription.status = status
                
            prescription.save()
            
            messages.success(request, "Prescription updated successfully.")
            return redirect('provider_prescriptions')
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider.user.last_name}",
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    return render(request, 'provider/edit_prescription.html', context)
