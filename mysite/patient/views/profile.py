from django.shortcuts import render, redirect
from django.contrib import messages
from theme_name.repositories import PatientRepository
from patient.forms import PatientProfileEditForm

def patient_profile(request):
    """Patient profile view"""
    patient = PatientRepository.get_current(request)
    
    if request.method == 'POST':
        form = PatientProfileEditForm(request.POST)
        if form.is_valid():
            # Get cleaned data from form
            updated_data = form.cleaned_data
            
            # Update patient data via repository
            PatientRepository.update(patient['id'], updated_data)
            
            # Get updated patient data
            patient = PatientRepository.get_by_id(patient['id'])
            
            # Add success message
            messages.success(request, "Profile updated successfully!")
            
            # Redirect to profile page to prevent form resubmission
            return redirect('patient:patient_profile')
    else:
        # Pre-fill form with existing patient data
        form = PatientProfileEditForm(initial={
            'first_name': patient.get('first_name', ''),
            'last_name': patient.get('last_name', ''),
            'email': patient.get('email', ''),
            'primary_phone': patient.get('primary_phone', ''),
            'alternate_phone': patient.get('alternate_phone', ''),
            'address': patient.get('address', ''),
            'emergency_contact_name': patient.get('emergency_contact_name', ''),
            'emergency_contact_phone': patient.get('emergency_contact_phone', '')
        })
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_section': 'profile',
        'form': form
    }
    return render(request, "patient/profile.html", context)

def patient_medical_history(request):
    """Patient medical history view"""
    patient = PatientRepository.get_current(request)
    
    # Get medical history data
    # In a real implementation, this would use a service or repository
    medical_history = {}
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_section': 'medical_history',
        'medical_history': medical_history
    }
    return render(request, "patient/medical_history.html", context)

def patient_help_center(request):
    """Patient help center view"""
    patient = PatientRepository.get_current(request)
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_section': 'help_center'
    }
    return render(request, "patient/help_center.html", context)
