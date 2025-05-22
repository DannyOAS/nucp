# patient/services/search_service.py
from django.db.models import Q
from common.models import Appointment, Prescription, Message
from patient.models import Patient
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Service layer for patient search operations - OPTIMIZED"""
    
    @staticmethod
    def search_patient_data(patient_id, query):
        """
        OPTIMIZED: Search with efficient joins and indexed fields
        
        Args:
            patient_id: ID of the patient
            query: Search query string
            
        Returns:
            dict: Dictionary containing search results
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Search with proper joins and efficient filtering
            
            # Search appointments with provider info loaded
            appointments = Appointment.objects.filter(
                Q(patient=user) &
                (Q(reason__icontains=query) | 
                 Q(notes__icontains=query) |
                 Q(doctor__user__first_name__icontains=query) |
                 Q(doctor__user__last_name__icontains=query))
            ).select_related(
                'doctor',
                'doctor__user'
            ).order_by('-time')[:20]  # Limit results for performance
            
            # Search prescriptions with provider info loaded
            prescriptions = Prescription.objects.filter(
                Q(patient=user) &
                (Q(medication_name__icontains=query) |
                 Q(dosage__icontains=query) |
                 Q(instructions__icontains=query))
            ).select_related(
                'doctor',
                'doctor__user'
            ).order_by('-created_at')[:20]
            
            # Search messages with sender/recipient info loaded
            messages = Message.objects.filter(
                (Q(recipient=user) | Q(sender=user)) &
                (Q(subject__icontains=query) |
                 Q(content__icontains=query))
            ).select_related(
                'sender',
                'recipient'
            ).exclude(
                status='deleted'
            ).order_by('-created_at')[:20]
            
            return {
                'success': True,
                'appointments': appointments,
                'prescriptions': prescriptions,
                'messages': messages
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'appointments': [],
                'prescriptions': [],
                'messages': []
            }
        except Exception as e:
            logger.error(f"Error in search_patient_data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'appointments': [],
                'prescriptions': [],
                'messages': []
            }
