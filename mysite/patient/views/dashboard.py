# patient/views/dashboard.py
from django.shortcuts import render
from patient.decorators import patient_required
from common.models import Message, Appointment, Prescription

# Uncomment for API-based implementation
# import requests
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def patient_dashboard(request):
    """Patient dashboard view using database models"""
    patient = request.patient  # Injected by decorator
    
    # Get recent appointments - use request.user since Appointment.patient is a User FK
    appointments = Appointment.objects.filter(patient=request.user).order_by('-time')[:5]
    
    # Get recent prescriptions - use request.user since Prescription.patient is a User FK
    prescriptions = Prescription.objects.filter(patient=request.user).order_by('-created_at')[:5]
    
    # Get recent messages
    recent_messages = Message.objects.filter(
        recipient=request.user
    ).exclude(
        status='deleted'
    ).order_by('-created_at')[:5]
    
    # Get unread message count
    unread_messages_count = Message.objects.filter(
        recipient=request.user, 
        status='unread'
    ).count()
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'appointments': appointments,
        'prescriptions': prescriptions,
        'recent_messages': recent_messages,
        'unread_messages_count': unread_messages_count,
        'active_section': 'dashboard',
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/patient/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get recent appointments
    #     appointments_response = requests.get(
    #         f"{api_url}appointments/?limit=5",
    #         headers=headers
    #     )
    #     appointments = appointments_response.json()['results'] if appointments_response.ok else []
    #     
    #     # Get recent prescriptions
    #     prescriptions_response = requests.get(
    #         f"{api_url}prescriptions/?limit=5",
    #         headers=headers
    #     )
    #     prescriptions = prescriptions_response.json()['results'] if prescriptions_response.ok else []
    #     
    #     # Get recent messages
    #     messages_response = requests.get(
    #         f"{api_url}messages/inbox/?limit=5",
    #         headers=headers
    #     )
    #     recent_messages = messages_response.json()['results'] if messages_response.ok else []
    #     
    #     # Get unread message count
    #     unread_count_response = requests.get(
    #         f"{api_url}messages/inbox/?status=unread&count_only=true",
    #         headers=headers
    #     )
    #     unread_messages_count = unread_count_response.json()['count'] if unread_count_response.ok else 0
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'appointments': appointments,
    #         'prescriptions': prescriptions,
    #         'recent_messages': recent_messages,
    #         'unread_messages_count': unread_messages_count,
    #         'active_section': 'dashboard',
    #     }
    # except Exception as e:
    #     # Handle API errors
    #     messages.error(request, f"Error loading dashboard data: {str(e)}")
    
    return render(request, "patient/dashboard.html", context)
