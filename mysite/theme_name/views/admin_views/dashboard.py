from django.shortcuts import render
from ...services import AIConfigurationService

def admin_dashboard(request):
    """Admin dashboard view"""
    # Get system stats and other dashboard data
    
    context = {
        'active_section': 'dashboard',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/dashboard.html", context)
