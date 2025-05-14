# patient/services/prescription_service.py
from patient.models import PrescriptionRequest
from common.models import Prescription

class PrescriptionService:
    @staticmethod
    def get_active_prescriptions(patient):
        """Get active prescriptions for a patient"""
        return Prescription.objects.filter(
            patient=patient.user,
            status='Active'
        ).order_by('-created_at')
    
    @staticmethod
    def get_all_prescriptions(patient):
        """Get all prescriptions for a patient"""
        return Prescription.objects.filter(
            patient=patient.user
        ).order_by('-created_at')
    
    @staticmethod
    def get_prescription_by_id(prescription_id):
        """Get a prescription by ID"""
        try:
            return Prescription.objects.get(id=prescription_id)
        except Prescription.DoesNotExist:
            return None
    
    @staticmethod
    def create_prescription_request(data, patient=None):
        """
        Create a new prescription request
        
        Args:
            data: Form data for prescription request
            patient: Patient model instance (optional)
            
        Returns:
            PrescriptionRequest: The created request
            or
            dict: Error details if request couldn't be created
        """
        try:
            # Handle patient assignment if provided
            if patient:
                prescription_request = PrescriptionRequest(
                    patient=patient,
                    medication_name=data.get('medication_name'),
                    current_dosage=data.get('current_dosage'),
                    medication_duration=data.get('medication_duration'),
                    last_refill_date=data.get('last_refill_date'),
                    preferred_pharmacy=data.get('preferred_pharmacy'),
                    new_medical_conditions=data.get('new_medical_conditions', ''),
                    new_medications=data.get('new_medications', ''),
                    side_effects=data.get('side_effects', ''),
                    information_consent=data.get('information_consent', False),
                    pharmacy_consent=data.get('pharmacy_consent', False),
                    status='pending'
                )
                prescription_request.save()
            else:
                # Use form directly for model creation
                prescription_request = data.save(commit=False)
                prescription_request.status = 'pending'
                prescription_request.save()
                
            return prescription_request
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def request_refill(prescription_id, refill_data, patient):
        """
        Request a prescription refill
        
        Args:
            prescription_id: ID of the prescription to refill
            refill_data: Form data for refill request
            patient: Patient model instance
            
        Returns:
            dict: Success or error information
        """
        try:
            # Get prescription and verify ownership
            prescription = Prescription.objects.get(id=prescription_id, patient=patient.user)
            
            # Check if refills are available
            if prescription.refills_remaining <= 0:
                return {
                    'success': False, 
                    'error': 'No refills remaining for this prescription'
                }
            
            # Create a refill request
            refill_request = PrescriptionRequest(
                patient=patient,
                medication_name=prescription.medication_name,
                current_dosage=prescription.dosage,
                medication_duration=refill_data.get('medication_duration', ''),
                last_refill_date=refill_data.get('last_dose_taken'),
                preferred_pharmacy=refill_data.get('pharmacy'),
                new_medical_conditions='',
                new_medications='',
                side_effects=refill_data.get('side_effects', ''),
                information_consent=refill_data.get('information_consent', False),
                pharmacy_consent=refill_data.get('pharmacy_consent', False),
                status='pending'
            )
            refill_request.save()
            
            # Update original prescription
            prescription.refills_remaining -= 1
            prescription.save()
            
            return {'success': True, 'request': refill_request}
            
        except Prescription.DoesNotExist:
            return {'success': False, 'error': 'Prescription not found or not authorized'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
