# patient/services/dashboard_service.py
from common.models import Appointment, Prescription, Message
from patient.models import Patient
from django.utils import timezone

class DashboardService:
    """Service layer for patient dashboard operations"""
    
    @staticmethod
    def get_dashboard_data(patient_id):
        """
        Get all data needed for patient dashboard
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing dashboard data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get upcoming appointments
            today = timezone.now()
            appointments = Appointment.objects.filter(
                patient=user,
                time__gte=today
            ).order_by('time')[:5]
            
            # Get recent prescriptions
            prescriptions = Prescription.objects.filter(
                patient=user
            ).order_by('-created_at')[:5]
            
            # Get recent messages
            recent_messages = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).order_by('-created_at')[:5]
            
            # Get unread message count
            unread_messages_count = Message.objects.filter(
                recipient=user, 
                status='unread'
            ).count()
            
            return {
                'success': True,
                'appointments': appointments,
                'prescriptions': prescriptions,
                'recent_messages': recent_messages,
                'unread_messages_count': unread_messages_count
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'appointments': [],
                'prescriptions': [],
                'recent_messages': [],
                'unread_messages_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'appointments': [],
                'prescriptions': [],
                'recent_messages': [],
                'unread_messages_count': 0
            }
