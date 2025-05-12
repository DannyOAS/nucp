# patient/views/profile.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
from patient.forms import PatientProfileEditForm

@patient_required
def patient_profile(request):
    """Patient profile view using database models"""
    patient = request.patient
    
    if request.method == 'POST':
        form = PatientProfileEditForm(request.POST, instance=patient)
        if form.is_valid():
            # Update User fields
            user = patient.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
            
            # Save patient profile
            form.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect('patient:patient_profile')
    else:
        # Pre-fill form with existing data
        initial_data = {
            'first_name': patient.user.first_name,
            'last_name': patient.user.last_name,
            'email': patient.user.email,
        }
        form = PatientProfileEditForm(instance=patient, initial=initial_data)
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'form': form,
        'active_section': 'profile',
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
