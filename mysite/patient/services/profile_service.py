# patient/services/profile_service.py
from patient.models import Patient
#from patient.forms import PatientProfileEditForm
from patient.forms import SecurePatientProfileEditForm as PatientProfileEditForm

class ProfileService:
    """Service layer for patient profile operations"""
    
    @staticmethod
    def get_profile_form_data(patient_id):
        """
        Get form data for patient profile
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Form data for patient profile
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Create form with initial data
            initial_data = {
                'first_name': patient.user.first_name,
                'last_name': patient.user.last_name,
                'email': patient.user.email,
            }
            form = PatientProfileEditForm(instance=patient, initial=initial_data)
            
            return {
                'success': True,
                'form': form
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'form': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'form': None
            }
    
    @staticmethod
    def update_patient_profile(patient_id, form_data, user):
        """
        Update patient profile with form data
        
        Args:
            patient_id: ID of the patient
            form_data: Form data for profile update
            user: User object for verification
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Verify user ownership
            if patient.user != user:
                return {
                    'success': False,
                    'error': 'Not authorized to update this profile'
                }
            
            # Create form with submitted data
            form = PatientProfileEditForm(form_data, instance=patient)
            
            if form.is_valid():
                # Update User fields
                user = patient.user
                user.first_name = form.cleaned_data.get('first_name', user.first_name)
                user.last_name = form.cleaned_data.get('last_name', user.last_name)
                user.email = form.cleaned_data.get('email', user.email)
                user.save()
                
                # Save patient profile
                form.save()
                
                return {
                    'success': True
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
    def get_medical_history(patient_id):
        """
        Get medical history for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Medical history data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # In a real implementation, this would retrieve medical history data
            # from the appropriate sources (EHR, etc.)
            # For now, we'll return a placeholder
            medical_history = {
                # Medical history structure would go here
                # This would be populated from various sources
            }
            
            return {
                'success': True,
                'medical_history': medical_history
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'medical_history': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'medical_history': {}
            }
