from django.shortcuts import render
from django.utils import timezone
from datetime import datetime
from theme_name.repositories import ProviderRepository, PrescriptionRepository, AppointmentRepository
from common.services.provider_service import ProviderService  # Add this line

def provider_dashboard(request):
    provider_id = 1  # In production, replace with request.user
    dashboard_data = ProviderService.get_dashboard_data(provider_id)
    context = {**dashboard_data, 'active_section': 'dashboard', 'today': datetime.now().date()}
    return render(request, "provider/dashboard.html", context)
