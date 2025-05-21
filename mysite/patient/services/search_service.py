# patient/services/search_service.py
from django.db.models import Q
from common.models import Appointment, Prescription, Message
from patient.models import Patient

class SearchService:
    """Service layer for patient search operations"""
    
    @staticmethod
    def search_patient_data(patient_id, query):
        """
        Search for patient's appointments, prescriptions, and messages
        
        Args:
            patient_id: ID of the patient
            query: Search query string
            
        Returns:
            dict: Dictionary containing search results
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Search appointments
            appointments = Appointment.objects.filter(
                Q(patient=user) &
                (Q(reason__icontains=query) | 
                 Q(notes__icontains=query) |
                 Q(doctor__user__first_name__icontains=query) |
                 Q(doctor__user__last_name__icontains=query))
            )
            
            # Search prescriptions
            prescriptions = Prescription.objects.filter(
                Q(patient=user) &
                (Q(medication_name__icontains=query) |
                 Q(dosage__icontains=query) |
                 Q(instructions__icontains=query))
            )
            
            # Search messages
            messages = Message.objects.filter(
                (Q(recipient=user) | Q(sender=user)) &
                (Q(subject__icontains=query) |
                 Q(content__icontains=query))
            ).exclude(status='deleted')
            
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
            return {
                'success': False,
                'error': str(e),
                'appointments': [],
                'prescriptions': [],
                'messages': []
            }
