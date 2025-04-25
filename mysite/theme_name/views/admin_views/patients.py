from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...data_access import get_all_patients

def admin_patients(request):
    """Admin patients management view"""
    # Get all patients
    patients = get_all_patients()
    
    # Search and filtering logic
    search_query = request.GET.get('search', '')
    if search_query:
        patients = [
            p for p in patients 
            if search_query.lower() in p.get('first_name', '').lower() or 
               search_query.lower() in p.get('last_name', '').lower() or
               search_query.lower() in p.get('email', '').lower() or
               search_query.lower() in p.get('ohip_number', '').lower()
        ]
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(patients, 10)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'patients': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_section': 'patients',
        'admin_name': 'Admin'
    }
    
    return render(request, "custom_admin/patients.html", context)
