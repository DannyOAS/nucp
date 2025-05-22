# patient/views/dashboard.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.dashboard_service import DashboardService
from patient.utils import get_current_patient
from api.v1.patient.serializers import (
    AppointmentSerializer, PrescriptionSerializer, MessageSerializer
)

logger = logging.getLogger(__name__)

@patient_required
def patient_dashboard(request):
    """
    Patient dashboard view displaying recent appointments, prescriptions and messages.
    Uses service layer to retrieve data and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get dashboard data from service
        dashboard_data = DashboardService.get_dashboard_data(patient.id)
        
        # Format appointments using API serializer if needed
        appointments = dashboard_data.get('appointments', [])
        if hasattr(appointments, 'model'):
            serializer = AppointmentSerializer(appointments, many=True)
            dashboard_data['appointments'] = serializer.data
        
        # Format prescriptions using API serializer if needed
        prescriptions = dashboard_data.get('prescriptions', [])
        if hasattr(prescriptions, 'model'):
            serializer = PrescriptionSerializer(prescriptions, many=True)
            dashboard_data['prescriptions'] = serializer.data
        
        # Format messages using API serializer if needed
        recent_messages = dashboard_data.get('recent_messages', [])
        if hasattr(recent_messages, 'model'):
            serializer = MessageSerializer(recent_messages, many=True)
            dashboard_data['recent_messages'] = serializer.data
        
        # GET HEALTH METRICS FROM DATABASE - NO HARDCODED DATA
        # You'll need to create a HealthMetric model or retrieve from existing models
        health_metrics = []
        # TODO: Replace with actual health metrics query when model exists
        # For now, just pass empty list - template should handle this gracefully
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'appointments': dashboard_data.get('appointments', []),
            'prescriptions': dashboard_data.get('prescriptions', []),
            'recent_messages': dashboard_data.get('recent_messages', []),
            'unread_messages_count': dashboard_data.get('unread_messages_count', 0),
            'health_metrics': health_metrics,  # Empty list until model exists
            'active_section': 'dashboard',
        }
    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'appointments': [],
            'prescriptions': [],
            'recent_messages': [],
            'unread_messages_count': 0,
            'health_metrics': [],  # Empty fallback
            'active_section': 'dashboard',
        }
        messages.error(request, "There was an error loading your dashboard. Please try again later.")
    
    return render(request, "patient/dashboard.html", context)
