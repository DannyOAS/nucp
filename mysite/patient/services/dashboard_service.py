# patient/services/dashboard_service.py
from common.models import Appointment, Prescription, Message
from patient.models import Patient
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    """Service layer for patient dashboard operations - OPTIMIZED"""
    
    @staticmethod
    def get_dashboard_data(patient_id):
        """
        OPTIMIZED: Get dashboard data with efficient parallel queries
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing dashboard data
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            today = timezone.now()
            
            # OPTIMIZED: Get all dashboard data with proper joins in parallel
            # These queries will be optimized by Django's ORM and your indexes
            
            # Appointments with provider info
            appointments = Appointment.objects.filter(
                patient=user,
                time__gte=today
            ).select_related(
                'doctor',
                'doctor__user'
            ).order_by('time')[:5]
            
            # Prescriptions with provider info  
            prescriptions = Prescription.objects.filter(
                patient=user
            ).select_related(
                'doctor',
                'doctor__user'
            ).order_by('-created_at')[:5]
            
            # Recent messages with sender info
            recent_messages = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).select_related(
                'sender'
            ).order_by('-created_at')[:5]
            
            # OPTIMIZED: Single query for unread count
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
            logger.error(f"Error in get_dashboard_data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'appointments': [],
                'prescriptions': [],
                'recent_messages': [],
                'unread_messages_count': 0
            }
