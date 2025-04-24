from django.shortcuts import render
from ...repositories import PatientRepository, MessageRepository
from ...models import Message

def patient_dashboard(request):
    """Patient dashboard view"""
    patient = PatientRepository.get_current(request)
    
    # Get dashboard data
    # In a real implementation, this would use PatientService.get_dashboard_data(patient['id'])
    dashboard_data = {
        'appointments': [],  # Will be populated from the repository
        'prescriptions': [],  # Will be populated from the repository
        'messages': []  # Will be populated from the repository
    }
    
    # Add messaging data for the dashboard
    unread_messages_count = 0
    recent_messages = []
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        # Get unread message count
        unread_messages_count = Message.objects.filter(
            recipient=request.user, 
            status='unread'
        ).count()
        
        # Get recent messages (limit to 2 for dashboard)
        recent_messages = Message.objects.filter(
            recipient=request.user
        ).exclude(
            status='deleted'
        ).order_by('-created_at')[:2]
    
    # Add message data to context
    dashboard_data['unread_messages_count'] = unread_messages_count
    dashboard_data['recent_messages'] = recent_messages
    
    context = {
        **dashboard_data,
        'active_section': 'dashboard',
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'patient': patient
    }
    
    return render(request, "patient/dashboard.html", context)

def get_base_context(active_section):
    """Helper function to get base context for patient views"""
    return {
        'active_section': active_section
    }
