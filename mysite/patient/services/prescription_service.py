# patient/services/prescription_service.py
from common.models import Prescription
from patient.models import Patient, PrescriptionRequest
from patient.forms import PrescriptionRequestForm
from django.utils import timezone

class PrescriptionService:
    """Service layer for patient prescription operations"""
    
    @staticmethod
    def get_patient_prescriptions(patient_id):
        """
        Get active and historical prescriptions for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing prescription data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get active prescriptions 
            active_prescriptions = Prescription.objects.filter(
                patient=user,
                status='Active'
            ).order_by('-created_at')
            
            # Get historical prescriptions
            historical_prescriptions = Prescription.objects.filter(
                patient=user
            ).exclude(
                status='Active'
            ).order_by('-created_at')
            
            return {
                'success': True,
                'active_prescriptions': active_prescriptions,
                'historical_prescriptions': historical_prescriptions
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'active_prescriptions': [],
                'historical_prescriptions': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'active_prescriptions': [],
                'historical_prescriptions': []
            }
    
    @staticmethod
    def get_prescription_details(prescription_id, patient_id):
        """
        Get details for a specific prescription
        
        Args:
            prescription_id: ID of the prescription
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result containing prescription data if successful
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get prescription and verify ownership
            prescription = Prescription.objects.get(id=prescription_id, patient=user)
            
            return {
                'success': True,
                'prescription': prescription
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Prescription.DoesNotExist:
            return {
                'success': False,
                'error': 'Prescription not found or not authorized'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_prescription_form_data(patient_id):
        """
        Get initial data for prescription request form
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Form initial data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Create form with initial data
            initial_data = {
                'first_name': patient.user.first_name,
                'last_name': patient.user.last_name,
                'date_of_birth': patient.date_of_birth,
                'ohip_number': patient.ohip_number,
                'phone_number': patient.primary_phone
            }
            
            form = PrescriptionRequestForm(initial=initial_data)
            
            return {
                'success': True,
                'form': form
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'form': PrescriptionRequestForm()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'form': PrescriptionRequestForm()
            }
    
    @staticmethod
    def create_prescription_request(patient_id, form_data):
        """
        Create a new prescription request
        
        Args:
            patient_id: ID of the patient
            form_data: Form data for prescription request
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Create form instance with submitted data
            form = PrescriptionRequestForm(form_data)
            
            if form.is_valid():
                # Create prescription request
                prescription_request = PrescriptionRequest(
                    patient=patient,
                    medication_name=form.cleaned_data['medication_name'],
                    current_dosage=form.cleaned_data['current_dosage'],
                    medication_duration=form.cleaned_data['medication_duration'],
                    last_refill_date=form.cleaned_data['last_refill_date'],
                    preferred_pharmacy=form.cleaned_data['preferred_pharmacy'],
                    new_medical_conditions=form.cleaned_data.get('new_medical_conditions', ''),
                    new_medications=form.cleaned_data.get('new_medications', ''),
                    side_effects=form.cleaned_data.get('side_effects', ''),
                    information_consent=form.cleaned_data.get('information_consent', False),
                    pharmacy_consent=form.cleaned_data.get('pharmacy_consent', False),
                    status='pending'
                )
                prescription_request.save()
                
                return {
                    'success': True,
                    'request': prescription_request
                }
            else:
                # Form validation failed
                errors = []
                for field, field_errors in form.errors.items():
                    errors.append(f"{field}: {', '.join(field_errors)}")
                
                return {
                    'success': False,
                    'error': 'Form validation failed: ' + '; '.join(errors)
                }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def request_refill(prescription_id, patient_id, refill_data):
        """
        Request a prescription refill
        
        Args:
            prescription_id: ID of the prescription to refill
            patient_id: ID of the patient (for ownership verification)
            refill_data: Form data for refill request
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get prescription and verify ownership
            prescription = Prescription.objects.get(id=prescription_id, patient=user)
            
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
            
            return {
                'success': True,
                'request': refill_request
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Prescription.DoesNotExist:
            return {
                'success': False,
                'error': 'Prescription not found or not authorized'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
