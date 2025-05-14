# patient/views/profile.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
from patient.forms import PatientProfileEditForm

# Uncomment for API-based implementation
# import requests
# import json
# from django.conf import settings
# from patient.utils import get_auth_header

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
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # if request.method == 'POST':
    #     form = PatientProfileEditForm(request.POST)
    #     if form.is_valid():
    #         try:
    #             # Prepare API payload
    #             payload = {
    #                 'user': {
    #                     'first_name': form.cleaned_data['first_name'],
    #                     'last_name': form.cleaned_data['last_name'],
    #                     'email': form.cleaned_data['email']
    #                 },
    #                 'primary_phone': form.cleaned_data['primary_phone'],
    #                 'alternate_phone': form.cleaned_data['alternate_phone'],
    #                 'address': form.cleaned_data['address'],
    #                 'emergency_contact_name': form.cleaned_data['emergency_contact_name'],
    #                 'emergency_contact_phone': form.cleaned_data['emergency_contact_phone']
    #             }
    #             
    #             # Update profile via API
    #             response = requests.patch(
    #                 f"{api_url}profile/me/",
    #                 headers=headers,
    #                 json=payload
    #             )
    #             
    #             if response.ok:
    #                 messages.success(request, "Profile updated successfully!")
    #                 return redirect('patient:patient_profile')
    #             else:
    #                 error_message = response.json().get('detail', 'Please try again.')
    #                 messages.error(request, f"Error updating profile: {error_message}")
    #         except Exception as e:
    #             messages.error(request, f"Error updating profile: {str(e)}")
    #     # If form is invalid, it will be rendered with errors
    # else:
    #     # Get profile data from API
    #     try:
    #         response = requests.get(
    #             f"{api_url}profile/me/",
    #             headers=headers
    #         )
    #         
    #         if response.ok:
    #             profile_data = response.json()
    #             initial_data = {
    #                 'first_name': profile_data['user']['first_name'],
    #                 'last_name': profile_data['user']['last_name'],
    #                 'email': profile_data['user']['email'],
    #                 'primary_phone': profile_data['primary_phone'],
    #                 'alternate_phone': profile_data['alternate_phone'],
    #                 'address': profile_data['address'],
    #                 'emergency_contact_name': profile_data['emergency_contact_name'],
    #                 'emergency_contact_phone': profile_data['emergency_contact_phone']
    #             }
    #             form = PatientProfileEditForm(initial=initial_data)
    #         else:
    #             form = PatientProfileEditForm()
    #             messages.error(request, "Error loading profile data.")
    #     except Exception as e:
    #         form = PatientProfileEditForm()
    #         messages.error(request, f"Error loading profile data: {str(e)}")
    # 
    # context = {
    #     'patient': patient,
    #     'patient_name': patient.full_name,
    #     'form': form,
    #     'active_section': 'profile',
    # }
    
    return render(request, "patient/profile.html", context)

@patient_required
def patient_medical_history(request):
    """Patient medical history view"""
    patient = request.patient
    
    # Get medical history data
    # In a real implementation, this would use a service or repository
    medical_history = {}
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'active_section': 'medical_history',
        'medical_history': medical_history
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get medical history from API
    #     response = requests.get(
    #         f"{api_url}medical-history/",
    #         headers=headers
    #     )
    #     
    #     if response.ok:
    #         medical_history = response.json()
    #     else:
    #         medical_history = {}
    #         messages.warning(request, "Could not load medical history data.")
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'active_section': 'medical_history',
    #         'medical_history': medical_history
    #     }
    # except Exception as e:
    #     messages.error(request, f"Error loading medical history: {str(e)}")
    
    return render(request, "patient/medical_history.html", context)
