from django.shortcuts import render
from ...services import AIConfigurationService
from ...data_access import get_current_admin, get_system_stats, get_admin_logs

def admin_dashboard(request):
    admin = get_current_admin(request)
    stats = get_system_stats()
    logs = get_admin_logs(limit=10)
    return render(request, "custom_admin/dashboard.html", {
        'admin': admin,
        'stats': stats,
        'logs': logs
    })
