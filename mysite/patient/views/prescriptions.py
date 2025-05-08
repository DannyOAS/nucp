from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from theme_name.repositories import PatientRepository, PrescriptionRepository
from common.services import PrescriptionService
from theme_name.forms import PrescriptionRequestForm

def patient_prescriptions(request):
    """Patient prescriptions view"""
    patient = PatientRepository.get_current(request)
    
    # Get prescriptions data
    active_prescriptions = PrescriptionRepository.get_active_for_patient(patient['id'])
    historical_prescriptions = PrescriptionRepository.get_historical_for_patient(patient['id'])
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_prescriptions': active_prescriptions,
        'historical_prescriptions': historical_prescriptions,
        'active_section': 'prescriptions'
    }
    
    return render(request, "patient/prescriptions.html", context)

def request_prescription(request):
    """Request a new prescription"""
    patient = PatientRepository.get_current(request)
    
    if request.method == 'POST':
        form = PrescriptionRequestForm(request.POST)
        if form.is_valid():
            prescription_request = form.save()
            messages.success(request, "Prescription request submitted successfully!")
            return redirect('patient:patient_prescriptions')
    else:
        # Pre-fill form with patient data
        form = PrescriptionRequestForm(initial={
            'first_name': patient.get('first_name', ''),
            'last_name': patient.get('last_name', ''),
            'date_of_birth': patient.get('date_of_birth', ''),
            'ohip_number': patient.get('ohip_number', ''),
            'phone_number': patient.get('primary_phone', '')
        })
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'form': form,
        'active_section': 'prescriptions'
    }
    
    return render(request, "patient/request_prescription.html", context)
#
#def request_refill(request, prescription_id):
#    """Request a prescription refill"""
#    patient = PatientRepository.get_current(request)
#    prescription = PrescriptionRepository.get_by_id(prescription_id)
#    
#    if not prescription:
#        messages.error(request, "Prescription not found.")
#        return redirect('patient:patient_prescriptions')
#    
#    # Process refill request logic here
#    
#    messages.success(request, f"Refill request for {prescription['medication_name']} submitted successfully!")
#    return redirect('patient:patient_prescriptions')
def request_refill(request, prescription_id):
    """Request a prescription refill"""
    patient = PatientRepository.get_current(request)
    prescription = PrescriptionRepository.get_by_id(prescription_id)
    
    if not prescription:
        messages.error(request, "Prescription not found.")
        return redirect('patient:patient_prescriptions')
    
    if request.method == 'POST':
        # Process refill request logic here
        messages.success(request, f"Refill request for {prescription['medication_name']} submitted successfully!")
        return redirect('patient:patient_prescriptions')
    else:
        # Show the refill confirmation page for GET requests
        context = {
            'patient': patient,
            'patient_name': f"{patient['first_name']} {patient['last_name']}",
            'prescription': prescription,
            'active_section': 'prescriptions'
        }
        return render(request, "patient/request_refill.html", context)

def prescription_detail(request, prescription_id):
    """View prescription details"""
    patient = PatientRepository.get_current(request)
    prescription = PrescriptionRepository.get_by_id(prescription_id)
    
    if not prescription:
        messages.error(request, "Prescription not found.")
        return redirect('patient:patient_prescriptions')
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'prescription': prescription,
        'active_section': 'prescriptions'
    }
    
    return render(request, "patient/prescription_detail.html", context)
