from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...data_access import get_admin_logs

def admin_logs(request):
    """Admin logs view"""
    # Get system logs
    logs = get_admin_logs()
    
    # Filter logs if needed
    log_type = request.GET.get('type', 'all')
    if log_type != 'all':
        logs = [log for log in logs if log.get('action', '') == log_type.upper()]
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(logs, 20)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'log_type': log_type,
        'active_section': 'logs',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/logs.html", context)
