# patient/views/prescriptions.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.prescription_service import PrescriptionService
from patient.utils import get_current_patient
from api.v1.patient.serializers import PrescriptionSerializer

logger = logging.getLogger(__name__)
#
#@patient_required
#def patient_prescriptions(request):
#    """
#    Patient prescriptions view showing active and historical prescriptions.
#    Uses service layer to retrieve data and API serializers for formatting.
#    """
#    # Get the current patient
#    patient, patient_dict = get_current_patient(request)
#    
#    # If the function returns None, it has already redirected
#    if patient is None:
#        return redirect('unauthorized')
#    
#    try:
#        # Get prescriptions data from service
#        prescriptions_data = PrescriptionService.get_patient_prescriptions(patient.id)
#        
#        # Format prescriptions using API serializer if needed
#        active_prescriptions = prescriptions_data.get('active_prescriptions', [])
#        if hasattr(active_prescriptions, 'model'):
#            serializer = PrescriptionSerializer(active_prescriptions, many=True)
#            prescriptions_data['active_prescriptions'] = serializer.data
#        
#        historical_prescriptions = prescriptions_data.get('historical_prescriptions', [])
#        if hasattr(historical_prescriptions, 'model'):
#            serializer = PrescriptionSerializer(historical_prescriptions, many=True)
#            prescriptions_data['historical_prescriptions'] = serializer.data
#        
#        context = {
#            'patient': patient_dict,
#            'patient_name': patient.full_name,
#            'active_prescriptions': prescriptions_data.get('active_prescriptions', []),
#            'historical_prescriptions': prescriptions_data.get('historical_prescriptions', []),
#            'active_section': 'prescriptions'
#        }
#    except Exception as e:
#        logger.error(f"Error retrieving prescriptions: {str(e)}")
#        context = {
#            'patient': patient_dict,
#            'patient_name': patient.full_name,
#            'active_prescriptions': [],
#            'historical_prescriptions': [],
#            'active_section': 'prescriptions'
#        }
#        messages.error(request, "There was an error loading your prescriptions. Please try again later.")
#    
#    return render(request, "patient/prescriptions.html", context)
@patient_required
def patient_prescriptions(request):
    """
    Patient prescriptions view showing active and historical prescriptions.
    Uses service layer to retrieve data and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get prescriptions data from service
        prescriptions_data = PrescriptionService.get_patient_prescriptions(patient.id)
        
        # Format prescriptions using API serializer if needed
        active_prescriptions = prescriptions_data.get('active_prescriptions', [])
        if hasattr(active_prescriptions, 'model'):
            serializer = PrescriptionSerializer(active_prescriptions, many=True)
            prescriptions_data['active_prescriptions'] = serializer.data
        
        historical_prescriptions = prescriptions_data.get('historical_prescriptions', [])
        if hasattr(historical_prescriptions, 'model'):
            serializer = PrescriptionSerializer(historical_prescriptions, many=True)
            prescriptions_data['historical_prescriptions'] = serializer.data
        
        # Calculate additional context variables
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'active_prescriptions': prescriptions_data.get('active_prescriptions', []),
            'historical_prescriptions': prescriptions_data.get('historical_prescriptions', []),
            'active_section': 'prescriptions',
            
            # Additional context variables
            'active_prescriptions_count': len(active_prescriptions),
            'prescriptions_needing_renewal_count': len([
                p for p in active_prescriptions 
                if p.get('status') == 'Renewal Soon' or p.get('refills_remaining') <= 1
            ]),
            'primary_pharmacy': patient.pharmacy_details if hasattr(patient, 'pharmacy_details') else 'Not Set',
            'primary_pharmacy_details': {
                'name': patient.pharmacy_details if hasattr(patient, 'pharmacy_details') else 'Northern Pharmacy',
                'address': getattr(patient, 'address', '123 Health Street'),
                'phone': getattr(patient, 'primary_phone', '(555) 123-4567')
            },
            'pharmacy_delivery_info': 'Home delivery available for eligible prescriptions.'
        }
    except Exception as e:
        logger.error(f"Error retrieving prescriptions: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'active_prescriptions': [],
            'historical_prescriptions': [],
            'active_section': 'prescriptions',
            
            # Fallback context variables
            'active_prescriptions_count': 0,
            'prescriptions_needing_renewal_count': 0,
            'primary_pharmacy': 'Not Set',
            'primary_pharmacy_details': {
                'name': 'Northern Pharmacy',
                'address': '',
                'phone': ''
            },
            'pharmacy_delivery_info': 'Home delivery not currently available.'
        }
        messages.error(request, "There was an error loading your prescriptions. Please try again later.")
    
    return render(request, "patient/prescriptions.html", context)

@patient_required
def request_prescription(request):
    """
    View for patient to request a new prescription.
    Uses service layer for form handling and request creation.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process prescription request via service
            result = PrescriptionService.create_prescription_request(
                patient_id=patient.id,
                form_data=request.POST
            )
            
            if result.get('success', False):
                messages.success(request, "Prescription request submitted successfully!")
                return redirect('patient:patient_prescriptions')
            else:
                messages.error(request, result.get('error', "Error submitting prescription request."))
        except Exception as e:
            logger.error(f"Error submitting prescription request: {str(e)}")
            messages.error(request, f"Error submitting prescription request: {str(e)}")
    
    # For GET requests, prepare the form with initial data
    try:
        # Get form initial data from service
        form_data = PrescriptionService.get_prescription_form_data(patient.id)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'form': form_data.get('form', {}),
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error preparing prescription form: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'form': {},
            'active_section': 'prescriptions'
        }
        messages.error(request, "There was an error preparing the prescription request form.")
    
    return render(request, "patient/request_prescription.html", context)

@patient_required
def request_refill(request, prescription_id):
    """
    View for patient to request a prescription refill.
    Uses service layer for validation and request processing.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Verify prescription ownership and get details
        prescription_data = PrescriptionService.get_prescription_details(
            prescription_id=prescription_id,
            patient_id=patient.id
        )
        
        if not prescription_data.get('success', False):
            messages.error(request, prescription_data.get('error', "Prescription not found."))
            return redirect('patient:patient_prescriptions')
        
        # Format prescription data using serializer if needed
        prescription = prescription_data.get('prescription')
        if prescription and hasattr(prescription, '__dict__'):
            serializer = PrescriptionSerializer(prescription)
            prescription = serializer.data
        
        if request.method == 'POST':
            # Process refill request via service
            refill_data = {
                'pharmacy': request.POST.get('pharmacy'),
                'last_dose_taken': request.POST.get('last_dose_taken'),
                'medication_changes': request.POST.get('medication_changes'),
                'changes_description': request.POST.get('changes_description', ''),
                'side_effects': request.POST.get('side_effects', ''),
                'notes': request.POST.get('notes', ''),
                'information_consent': 'information_consent' in request.POST,
                'pharmacy_consent': 'pharmacy_consent' in request.POST
            }
            
            result = PrescriptionService.request_refill(
                prescription_id=prescription_id,
                patient_id=patient.id,
                refill_data=refill_data
            )
            
            if result.get('success', False):
                messages.success(request, f"Refill request for {prescription.get('medication_name')} submitted successfully!")
                return redirect('patient:patient_prescriptions')
            else:
                messages.error(request, result.get('error', "Error requesting refill."))
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'prescription': prescription,
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error processing refill request: {str(e)}")
        messages.error(request, "There was an error processing your refill request.")
        return redirect('patient:patient_prescriptions')
    
    return render(request, "patient/request_refill.html", context)

@patient_required
def prescription_detail(request, prescription_id):
    """
    View prescription details with full information.
    Uses service layer for data retrieval and verification.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get prescription details from service
        prescription_data = PrescriptionService.get_prescription_details(
            prescription_id=prescription_id,
            patient_id=patient.id
        )
        
        if not prescription_data.get('success', False):
            messages.error(request, prescription_data.get('error', "Prescription not found."))
            return redirect('patient:patient_prescriptions')
        
        # Format prescription data using serializer if needed
        prescription = prescription_data.get('prescription')
        if prescription and hasattr(prescription, '__dict__'):
            serializer = PrescriptionSerializer(prescription)
            prescription = serializer.data
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'prescription': prescription,
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error retrieving prescription details: {str(e)}")
        messages.error(request, "There was an error retrieving the prescription details.")
        return redirect('patient:patient_prescriptions')
    
    return render(request, "patient/prescription_detail.html", context)
