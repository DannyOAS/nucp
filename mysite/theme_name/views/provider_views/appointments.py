from django.shortcuts import render
from ...repositories import ProviderRepository

def provider_appointments(request):
    """Provider appointments view"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get appointments
    appointments = ProviderRepository.get_appointments(provider_id)
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'appointments': appointments,
        'active_section': 'appointments'
    }
    
    return render(request, "provider/appointments.html", context)
