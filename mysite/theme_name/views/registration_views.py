from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from ..forms import (
    PatientRegistrationForm, ProviderRegistrationForm, 
    PrescriptionRequestForm, DemoRequestForm
)
from ..models import PatientRegistration

def registration_view(request):
    """Main registration view"""
    return render(request, "registration.html")

def prescription_view(request):
    """Prescription request view"""
    if request.method == 'POST':
        form = PrescriptionRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription request submitted successfully!')
            return redirect('prescription_success')
    else:
        form = PrescriptionRequestForm()
    return render(request, "prescription.html", {'form': form})

def login_view(request):
    """Login view"""
    # Placeholder for your actual login implementation
    return render(request, "login.html")

def register_selection(request):
    """View for selecting registration type (patient or provider)"""
    return render(request, "register_selection.html")

def patient_registration(request):
    """Patient registration view"""
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # Save patient registration
            registration = form.save()
            
            # You could add additional processing here
            # Such as cloud uploads or ERP syncing as shown in your original code
            
            messages.success(
                request,
                'Registration submitted successfully! Your information has been processed.'
            )
            return redirect('registration_success')
    else:
        form = PatientRegistrationForm()
    return render(request, "patient_registration.html", {'form': form})

def provider_registration(request):
    """Provider registration view"""
    if request.method == 'POST':
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            # Save provider registration
            registration = form.save()
            
            messages.success(
                request,
                'Provider registration submitted successfully! Your information has been processed.'
            )
            return redirect('registration_success')
    else:
        form = ProviderRegistrationForm()
    return render(request, "provider_registration.html", {'form': form})

def registration_success(request):
    """Registration success page"""
    return render(request, "registration_success.html")

def schedule_demo(request):
    """Handle demo scheduling requests"""
    if request.method == "POST":
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            try:
                demo_request = form.save()
                
                # Send email notification logic would go here
                # send_mail(...)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Your demo request has been submitted successfully! We will contact you shortly to confirm.'
                })
            except Exception as e:
                print(f"Error saving form: {e}")  # Log the error
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [f"Server error: {str(e)}"]}
                }, status=500)
        else:
            print(f"Form validation errors: {form.errors}")  # Log validation errors
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = DemoRequestForm()
    
    form_html = render_to_string('partials/demo_form.html', {'form': form})
    return JsonResponse({'form_html': form_html})

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')
