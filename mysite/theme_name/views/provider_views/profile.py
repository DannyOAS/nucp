from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from ...repositories import ProviderRepository, PrescriptionRepository, AppointmentRepository

def provider_profile(request):
    """Provider profile page with edit functionality"""
    provider_id = 1  # In production, replace with request.user.id
    provider = ProviderRepository.get_by_id(provider_id)
    
    if request.method == 'POST':
        form = ProviderProfileEditForm(request.POST)
        if form.is_valid():
            # Get cleaned data from form
            updated_data = form.cleaned_data
            
            # Update provider data via repository
            ProviderRepository.update(provider_id, updated_data)
            
            # Get updated provider data
            provider = ProviderRepository.get_by_id(provider_id)
            
            # Add success message
            messages.success(request, "Profile updated successfully!")
            
            # Redirect to profile page to prevent form resubmission
            return redirect('provider_profile')
    else:
        # Pre-fill form with existing provider data
        form = ProviderProfileEditForm(initial={
            'first_name': provider.get('first_name', ''),
            'last_name': provider.get('last_name', ''),
            'email': provider.get('email', ''),
            'phone': provider.get('phone', ''),
            'specialty': provider.get('specialty', ''),
            'bio': provider.get('bio', '')
        })
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'profile',
        'form': form
    }
    return render(request, "provider/profile.html", context)

def provider_settings(request):
    """Provider settings page"""
    provider_id = 1  # In production, replace with request.user.id
    provider = ProviderRepository.get_by_id(provider_id)
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'settings'
    }
    return render(request, "provider/settings.html", context)

def provider_help_support(request):
    """Provider help and support page"""
    provider_id = 1  # In production, replace with request.user.id
    provider = ProviderRepository.get_by_id(provider_id)
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'help_support'
    }
    return render(request, "provider/help_support.html", context)
