# patient/views/prescriptions.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from patient.decorators import patient_required
from common.models import Prescription
from patient.models import PrescriptionRequest
from patient.forms import PrescriptionRequestForm
from patient.services.prescription_service import PrescriptionService

# Uncomment for API-based implementation
# import requests
# import json
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def patient_prescriptions(request):
    """Patient prescriptions view using database models"""
    patient = request.patient
    
    # Get prescriptions data
    active_prescriptions = Prescription.objects.filter(
        patient=request.user,
        status='Active'
    ).order_by('-created_at')
    
    historical_prescriptions = Prescription.objects.filter(
        patient=request.user
    ).exclude(
        status='Active'
    ).order_by('-created_at')
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'active_prescriptions': active_prescriptions,
        'historical_prescriptions': historical_prescriptions,
        'active_section': 'prescriptions'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get active prescriptions
    #     active_response = requests.get(
    #         f"{api_url}prescriptions/active/",
    #         headers=headers
    #     )
    #     active_prescriptions = active_response.json()['results'] if active_response.ok else []
    #     
    #     # Get historical prescriptions
    #     historical_response = requests.get(
    #         f"{api_url}prescriptions/?status=!Active",
    #         headers=headers
    #     )
    #     historical_prescriptions = historical_response.json()['results'] if historical_response.ok else []
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'active_prescriptions': active_prescriptions,
    #         'historical_prescriptions': historical_prescriptions,
    #         'active_section': 'prescriptions'
    #     }
    # except Exception as e:
    #     # Handle API errors
    #     messages.error(request, f"Error loading prescriptions: {str(e)}")
    
    return render(request, "patient/prescriptions.html", context)

@patient_required
def request_prescription(request):
    """Request a new prescription"""
    patient = request.patient
    
    if request.method == 'POST':
        form = PrescriptionRequestForm(request.POST)
        if form.is_valid():
            # Use the service to create the prescription request
            result = PrescriptionService.create_prescription_request(form, patient)
            
            if not isinstance(result, dict):  # Not an error
                messages.success(request, "Prescription request submitted successfully!")
                return redirect('patient:patient_prescriptions')
            else:
                messages.error(request, f"Error submitting prescription request: {result.get('error', 'Please try again.')}")
    else:
        # Pre-fill form with patient data
        form = PrescriptionRequestForm(initial={
            'first_name': patient.user.first_name,
            'last_name': patient.user.last_name,
            'date_of_birth': patient.date_of_birth,
            'ohip_number': patient.ohip_number,
            'phone_number': patient.primary_phone
        })
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'form': form,
        'active_section': 'prescriptions'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # if request.method == 'POST':
    #     form = PrescriptionRequestForm(request.POST)
    #     if form.is_valid():
    #         try:
    #             # Create API payload
    #             payload = {
    #                 'medication_name': form.cleaned_data['medication_name'],
    #                 'current_dosage': form.cleaned_data['current_dosage'],
    #                 'medication_duration': form.cleaned_data['medication_duration'],
    #                 'last_refill_date': form.cleaned_data['last_refill_date'].isoformat() if form.cleaned_data['last_refill_date'] else None,
    #                 'preferred_pharmacy': form.cleaned_data['preferred_pharmacy'],
    #                 'new_medical_conditions': form.cleaned_data['new_medical_conditions'],
    #                 'new_medications': form.cleaned_data['new_medications'],
    #                 'side_effects': form.cleaned_data['side_effects'],
    #                 'information_consent': form.cleaned_data['information_consent'],
    #                 'pharmacy_consent': form.cleaned_data['pharmacy_consent']
    #             }
    #             
    #             # Submit request to API
    #             response = requests.post(
    #                 f"{api_url}prescription-requests/",
    #                 headers=headers,
    #                 json=payload
    #             )
    #             
    #             if response.ok:
    #                 messages.success(request, "Prescription request submitted successfully!")
    #                 return redirect('patient:patient_prescriptions')
    #             else:
    #                 error_message = response.json().get('detail', 'Please try again.')
    #                 messages.error(request, f"Error submitting prescription request: {error_message}")
    #                 
    #         except Exception as e:
    #             messages.error(request, f"Error submitting prescription request: {str(e)}")
    #     else:
    #         # Form is invalid, display errors
    #         pass
    # else:
    #     # Pre-fill form with patient data from API
    #     try:
    #         response = requests.get(
    #             f"{api_url}profile/me/",
    #             headers=headers
    #         )
    #         
    #         if response.ok:
    #             profile_data = response.json()
    #             initial_data = {
    #                 'first_name': profile_data.get('user', {}).get('first_name', ''),
    #                 'last_name': profile_data.get('user', {}).get('last_name', ''),
    #                 'date_of_birth': profile_data.get('date_of_birth', ''),
    #                 'ohip_number': profile_data.get('ohip_number', ''),
    #                 'phone_number': profile_data.get('primary_phone', '')
    #             }
    #             form = PrescriptionRequestForm(initial=initial_data)
    #         else:
    #             form = PrescriptionRequestForm()
    #     except Exception as e:
    #         messages.error(request, f"Error loading patient data: {str(e)}")
    #         form = PrescriptionRequestForm()
    # 
    # context = {
    #     'patient': patient,
    #     'patient_name': patient.full_name,
    #     'form': form,
    #     'active_section': 'prescriptions'
    # }
    
    return render(request, "patient/request_prescription.html", context)

@patient_required
def request_refill(request, prescription_id):
    """Request a prescription refill"""
    patient = request.patient
    
    # Get the prescription
    try:
        prescription = Prescription.objects.get(id=prescription_id, patient=request.user)
    except Prescription.DoesNotExist:
        messages.error(request, "Prescription not found.")
        return redirect('patient:patient_prescriptions')
    
    if request.method == 'POST':
        # Use the service to request a refill
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
            refill_data=refill_data,
            patient=patient
        )
        
        if result.get('success'):
            messages.success(request, f"Refill request for {prescription.medication_name} submitted successfully!")
            return redirect('patient:patient_prescriptions')
        else:
            messages.error(request, f"Error requesting refill: {result.get('error', 'Please try again.')}")
    
    # For GET requests, show the refill confirmation page
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get prescription details
    #     prescription_response = requests.get(
    #         f"{api_url}prescriptions/{prescription_id}/",
    #         headers=headers
    #     )
    #     
    #     if not prescription_response.ok:
    #         messages.error(request, "Prescription not found or you don't have permission to view it.")
    #         return redirect('patient:patient_prescriptions')
    #     
    #     prescription = prescription_response.json()
    #     
    #     if request.method == 'POST':
    #         # Create API payload
    #         payload = {
    #             'prescription_id': prescription_id,
    #             'pharmacy': request.POST.get('pharmacy'),
    #             'last_dose_taken': request.POST.get('last_dose_taken'),
    #             'medication_changes': request.POST.get('medication_changes'),
    #             'changes_description': request.POST.get('changes_description', ''),
    #             'side_effects': request.POST.get('side_effects', ''),
    #             'notes': request.POST.get('notes', ''),
    #             'information_consent': 'information_consent' in request.POST,
    #             'pharmacy_consent': 'pharmacy_consent' in request.POST
    #         }
    #         
    #         # Submit refill request to API
    #         refill_response = requests.post(
    #             f"{api_url}prescriptions/{prescription_id}/refill/",
    #             headers=headers,
    #             json=payload
    #         )
    #         
    #         if refill_response.ok:
    #             messages.success(request, f"Refill request for {prescription['medication_name']} submitted successfully!")
    #             return redirect('patient:patient_prescriptions')
    #         else:
    #             error_message = refill_response.json().get('detail', 'Please try again.')
    #             messages.error(request, f"Error requesting refill: {error_message}")
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'prescription': prescription,
    #         'active_section': 'prescriptions'
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading prescription data: {str(e)}")
    #     return redirect('patient:patient_prescriptions')
    
    return render(request, "patient/request_refill.html", context)

@patient_required
def prescription_detail(request, prescription_id):
    """View prescription details"""
    patient = request.patient
    
    # Get the prescription
    try:
        prescription = Prescription.objects.get(id=prescription_id, patient=request.user)
    except Prescription.DoesNotExist:
        messages.error(request, "Prescription not found.")
        return redirect('patient:patient_prescriptions')
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get prescription details
    #     prescription_response = requests.get(
    #         f"{api_url}prescriptions/{prescription_id}/",
    #         headers=headers
    #     )
    #     
    #     if not prescription_response.ok:
    #         messages.error(request, "Prescription not found or you don't have permission to view it.")
    #         return redirect('patient:patient_prescriptions')
    #     
    #     prescription = prescription_response.json()
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'prescription': prescription,
    #         'active_section': 'prescriptions'
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading prescription details: {str(e)}")
    #     return redirect('patient:patient_prescriptions')
    
    return render(request, "patient/prescription_detail.html", context)
