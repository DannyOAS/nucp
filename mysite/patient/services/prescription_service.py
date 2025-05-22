# patient/services/prescription_service.py
from common.models import Prescription
from patient.models import Patient, PrescriptionRequest
from patient.forms import PrescriptionRequestForm
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class PrescriptionService:
    """Service layer for patient prescription operations"""

    @staticmethod
    def get_patient_prescriptions(patient_id):
        """
        OPTIMIZED: Get prescriptions with efficient single queries
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            try:
                # OPTIMIZED: Single query with join to provider for active prescriptions
                active_prescriptions = Prescription.objects.filter(
                    patient=user,
                    status='Active'
                ).select_related(
                    'doctor',
                    'doctor__user'
                ).order_by('-created_at')
                
                # OPTIMIZED: Single query with join to provider for historical prescriptions  
                historical_prescriptions = Prescription.objects.filter(
                    patient=user
                ).exclude(
                    status='Active'
                ).select_related(
                    'doctor',
                    'doctor__user'
                ).order_by('-created_at')[:20]  # Limit for performance
                
                # Convert to consistent format with optimized data access
                active_list = []
                for prescription in active_prescriptions:
                    active_list.append({
                        'id': prescription.id,
                        'medication_name': prescription.medication_name,
                        'dosage': prescription.dosage,
                        'status': prescription.status,
                        'refills_remaining': prescription.refills_remaining,
                        'created_at': prescription.created_at,
                        'prescribed_by': f"Dr. {prescription.doctor.user.last_name}" if prescription.doctor else 'Your Healthcare Provider',
                        'prescribed_date': prescription.created_at.date(),
                        'expires': prescription.expires or 'Not specified',
                        'pharmacy': 'Northern Pharmacy',  # Could be a field later
                        'instructions': prescription.instructions or 'Take as directed',
                        'side_effects': 'Consult your healthcare provider',
                        'warnings': 'Follow prescription instructions carefully'
                    })
                
                historical_list = []
                for prescription in historical_prescriptions:
                    historical_list.append({
                        'id': prescription.id,
                        'medication_name': prescription.medication_name,
                        'dosage': prescription.dosage,
                        'status': prescription.status,
                        'refills_remaining': prescription.refills_remaining,
                        'created_at': prescription.created_at,
                        'prescribed_by': f"Dr. {prescription.doctor.user.last_name}" if prescription.doctor else 'Your Healthcare Provider',
                        'prescribed_date': prescription.created_at.date(),
                        'expires': prescription.expires or 'Not specified',
                        'pharmacy': 'Northern Pharmacy',
                        'instructions': prescription.instructions or 'Take as directed',
                        'side_effects': 'Consult your healthcare provider',
                        'warnings': 'Follow prescription instructions carefully'
                    })
                
                return {
                    'success': True,
                    'active_prescriptions': active_list,
                    'historical_prescriptions': historical_list
                }
                
            except Exception as prescription_error:
                # Fallback to PrescriptionRequest - OPTIMIZED
                logger.warning(f"Prescription model error: {prescription_error}, falling back to PrescriptionRequest")
                
                # OPTIMIZED: Use select_related for patient relationship
                active_requests = PrescriptionRequest.objects.filter(
                    patient=patient,
                    status='approved'
                ).select_related('patient__user').order_by('-created_at')
                
                historical_requests = PrescriptionRequest.objects.filter(
                    patient=patient
                ).exclude(
                    status='approved'
                ).select_related('patient__user').order_by('-created_at')[:20]
                
                # Convert with optimized access
                active_prescriptions = [
                    {
                        'id': req.id,
                        'medication_name': req.medication_name,
                        'dosage': req.current_dosage,
                        'status': 'Active',
                        'refills_remaining': 3,
                        'created_at': req.created_at,
                        'prescribed_by': 'Your Healthcare Provider',
                        'prescribed_date': req.created_at.date(),
                        'expires': 'Not specified',
                        'pharmacy': req.preferred_pharmacy,
                        'instructions': 'Take as directed',
                        'side_effects': req.side_effects or 'Consult your healthcare provider',
                        'warnings': 'Follow prescription instructions carefully'
                    }
                    for req in active_requests
                ]
                
                historical_prescriptions = [
                    {
                        'id': req.id,
                        'medication_name': req.medication_name,
                        'dosage': req.current_dosage,
                        'status': req.status.title(),
                        'refills_remaining': 0,
                        'created_at': req.created_at,
                        'prescribed_by': 'Your Healthcare Provider',
                        'prescribed_date': req.created_at.date(),
                        'expires': 'Not specified',
                        'pharmacy': req.preferred_pharmacy,
                        'instructions': 'Take as directed',
                        'side_effects': req.side_effects or 'Consult your healthcare provider',
                        'warnings': 'Follow prescription instructions carefully'
                    }
                    for req in historical_requests
                ]
                
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
            
            try:
                # Try to get from Prescription model first
                prescription = Prescription.objects.get(id=prescription_id, patient=user)
                
                # Convert to dict format with all required fields
                prescription_data = {
                    'id': prescription.id,
                    'medication_name': getattr(prescription, 'medication_name', 'Unknown Medication'),
                    'dosage': getattr(prescription, 'dosage', 'Not specified'),
                    'status': getattr(prescription, 'status', 'Active'),
                    'refills_remaining': getattr(prescription, 'refills_remaining', 3),
                    'created_at': getattr(prescription, 'created_at', timezone.now()),
                    'prescribed_by': getattr(prescription, 'prescribed_by', 'Your Healthcare Provider'),
                    'prescribed_date': getattr(prescription, 'prescribed_date', prescription.created_at if hasattr(prescription, 'created_at') else timezone.now()),
                    'expires': getattr(prescription, 'expires', 'Not specified'),
                    'pharmacy': getattr(prescription, 'pharmacy', 'Northern Pharmacy'),
                    'instructions': getattr(prescription, 'instructions', 'Take as directed'),
                    'side_effects': getattr(prescription, 'side_effects', 'Consult your healthcare provider'),
                    'warnings': getattr(prescription, 'warnings', 'Follow prescription instructions carefully')
                }
                
                return {
                    'success': True,
                    'prescription': prescription_data
                }
                
            except Prescription.DoesNotExist:
                # FIXED: Fall back to PrescriptionRequest if Prescription not found
                try:
                    prescription_request = PrescriptionRequest.objects.get(id=prescription_id, patient=patient)
                    
                    # Convert to prescription-like format
                    prescription_data = {
                        'id': prescription_request.id,
                        'medication_name': prescription_request.medication_name,
                        'dosage': prescription_request.current_dosage,
                        'status': prescription_request.status.title(),
                        'refills_remaining': 3 if prescription_request.status == 'approved' else 0,
                        'created_at': prescription_request.created_at,
                        'prescribed_by': 'Your Healthcare Provider',
                        'prescribed_date': prescription_request.created_at,
                        'expires': 'Not specified',
                        'pharmacy': prescription_request.preferred_pharmacy,
                        'instructions': 'Take as directed',
                        'side_effects': prescription_request.side_effects or 'Consult your healthcare provider',
                        'warnings': 'Follow prescription instructions carefully'
                    }
                    
                    return {
                        'success': True,
                        'prescription': prescription_data
                    }
                    
                except PrescriptionRequest.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Prescription not found or not authorized'
                    }
                    
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Exception as e:
            logger.error(f"Error in get_prescription_details: {str(e)}")
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
            
            # FIXED: Don't include patient-related fields in initial data since they're removed from form
            initial_data = {
                'preferred_pharmacy': getattr(patient, 'pharmacy_details', 'Northern Pharmacy')
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
            logger.error(f"Error in get_prescription_form_data: {str(e)}")
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
            
            # FIXED: Create form instance with submitted data - exclude patient field
            form_data_copy = form_data.copy()
            if 'patient' in form_data_copy:
                del form_data_copy['patient']  # Remove patient field from form data
            
            form = PrescriptionRequestForm(form_data_copy)
            
            if form.is_valid():
                # FIXED: Create prescription request and set patient manually
                prescription_request = form.save(commit=False)  # Don't save yet
                prescription_request.patient = patient  # Set patient manually
                prescription_request.status = 'pending'
                prescription_request.save()  # Now save
                
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
            logger.error(f"Error in create_prescription_request: {str(e)}")
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
            
            # FIXED: Try to get prescription, fall back to prescription request
            prescription = None
            try:
                prescription = Prescription.objects.get(id=prescription_id, patient=user)
                prescription_name = getattr(prescription, 'medication_name', 'Unknown Medication')
                refills_remaining = getattr(prescription, 'refills_remaining', 0)
            except Prescription.DoesNotExist:
                # Try to get from PrescriptionRequest
                try:
                    prescription_request = PrescriptionRequest.objects.get(id=prescription_id, patient=patient)
                    prescription_name = prescription_request.medication_name
                    refills_remaining = 3 if prescription_request.status == 'approved' else 0
                except PrescriptionRequest.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Prescription not found or not authorized'
                    }
            
            # Check if refills are available
            if refills_remaining <= 0:
                return {
                    'success': False, 
                    'error': 'No refills remaining for this prescription'
                }
            
            # Create a refill request
            refill_request = PrescriptionRequest(
                patient=patient,
                medication_name=prescription_name,
                current_dosage=refill_data.get('current_dosage', 'As prescribed'),
                medication_duration=refill_data.get('medication_duration', 'Ongoing'),
                last_refill_date=refill_data.get('last_dose_taken'),
                preferred_pharmacy=refill_data.get('pharmacy', 'Northern Pharmacy'),
                new_medical_conditions='',
                new_medications='',
                side_effects=refill_data.get('side_effects', ''),
                information_consent=refill_data.get('information_consent', False),
                pharmacy_consent=refill_data.get('pharmacy_consent', False),
                status='pending'
            )
            refill_request.save()
            
            # Update original prescription if it exists
            if prescription:
                prescription.refills_remaining = max(0, refills_remaining - 1)
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
        except Exception as e:
            logger.error(f"Error in request_refill: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
