# patient/views/search.py
from django.shortcuts import render
from django.db.models import Q
from patient.decorators import patient_required
from common.models import Appointment, Prescription, Message

# Uncomment for API-based implementation
# import requests
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def patient_search(request):
    """View for patient search functionality"""
    patient = request.patient
    query = request.GET.get('query', '')
    results = {'appointments': [], 'prescriptions': [], 'messages': []}
    
    if query:
        # Search appointments
        appointments = Appointment.objects.filter(
            Q(patient=request.user) &
            (Q(reason__icontains=query) | 
             Q(notes__icontains=query) |
             Q(doctor__user__first_name__icontains=query) |
             Q(doctor__user__last_name__icontains=query))
        )
        
        # Search prescriptions
        prescriptions = Prescription.objects.filter(
            Q(patient=request.user) &
            (Q(medication_name__icontains=query) |
             Q(dosage__icontains=query) |
             Q(instructions__icontains=query))
        )
        
        # Search messages
        messages = Message.objects.filter(
            (Q(recipient=request.user) | Q(sender=request.user)) &
            (Q(subject__icontains=query) |
             Q(content__icontains=query))
        ).exclude(status='deleted')
        
        results = {
            'appointments': appointments,
            'prescriptions': prescriptions,
            'messages': messages
        }
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'query': query,
        'results': results,
        'active_section': 'search'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # if query:
    #     try:
    #         # Get search results from API
    #         search_response = requests.get(
    #             f"{api_url}search/?q={query}",
    #             headers=headers
    #         )
    #         
    #         if search_response.ok:
    #             results = search_response.json()
    #         else:
    #             results = {'appointments': [], 'prescriptions': [], 'messages': []}
    #     except Exception as e:
    #         messages.error(request, f"Error performing search: {str(e)}")
    #         results = {'appointments': [], 'prescriptions': [], 'messages': []}
    # else:
    #     results = {'appointments': [], 'prescriptions': [], 'messages': []}
    # 
    # context = {
    #     'patient': patient,
    #     'patient_name': patient.full_name,
    #     'query': query,
    #     'results': results,
    #     'active_section': 'search'
    # }
    
    return render(request, 'patient/search_results.html', context)
