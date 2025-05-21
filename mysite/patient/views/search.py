# patient/views/search.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.search_service import SearchService
from patient.utils import get_current_patient
from api.v1.patient.serializers import (
    AppointmentSerializer, PrescriptionSerializer, MessageSerializer
)

logger = logging.getLogger(__name__)

@patient_required
def patient_search(request):
    """
    Patient search view for finding appointments, prescriptions, and messages.
    Uses service layer for search functionality and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    # Get search query from request
    query = request.GET.get('query', '')
    results = {'appointments': [], 'prescriptions': [], 'messages': []}
    
    if query:
        try:
            # Perform search via service
            search_results = SearchService.search_patient_data(
                patient_id=patient.id,
                query=query
            )
            
            # Format search results using API serializers if needed
            appointments = search_results.get('appointments', [])
            if hasattr(appointments, 'model'):
                serializer = AppointmentSerializer(appointments, many=True)
                search_results['appointments'] = serializer.data
            
            prescriptions = search_results.get('prescriptions', [])
            if hasattr(prescriptions, 'model'):
                serializer = PrescriptionSerializer(prescriptions, many=True)
                search_results['prescriptions'] = serializer.data
            
            messages_list = search_results.get('messages', [])
            if hasattr(messages_list, 'model'):
                serializer = MessageSerializer(messages_list, many=True)
                search_results['messages'] = serializer.data
            
            results = {
                'appointments': search_results.get('appointments', []),
                'prescriptions': search_results.get('prescriptions', []),
                'messages': search_results.get('messages', [])
            }
            
            # Check if no results found
            if (len(results['appointments']) == 0 and 
                len(results['prescriptions']) == 0 and 
                len(results['messages']) == 0):
                messages.info(request, f"No results found for '{query}'.")
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            messages.error(request, "There was an error processing your search. Please try again.")
    
    context = {
        'patient': patient_dict,
        'patient_name': patient.full_name,
        'query': query,
        'results': results,
        'active_section': 'search'
    }
    
    return render(request, 'patient/search_results.html', context)
