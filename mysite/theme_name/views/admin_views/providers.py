from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ...data_access import get_all_providers

def admin_providers(request):
    """Admin providers management view"""
    # Get all providers
    providers = get_all_providers()
    
    # Search and filtering logic
    search_query = request.GET.get('search', '')
    if search_query:
        providers = [
            p for p in providers 
            if search_query.lower() in p.get('first_name', '').lower() or 
               search_query.lower() in p.get('last_name', '').lower() or
               search_query.lower() in p.get('email', '').lower() or
               search_query.lower() in p.get('specialty', '').lower()
        ]
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(providers, 10)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'providers': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_section': 'providers',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/providers.html", context)
