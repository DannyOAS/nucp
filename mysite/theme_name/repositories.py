# repositories.py

from django.conf import settings
from datetime import datetime, timedelta
import logging
from .data_access import (
    get_current_patient, get_patient_by_id, get_all_patients,
    get_patient_prescriptions, get_prescription_by_id, get_all_prescriptions, save_prescription_request,
    get_patient_appointments, get_appointment_by_id, get_all_appointments,
    get_patient_messages, get_message_by_id, get_all_messages,
    search_patient_data,
    get_provider_by_id, get_provider_patients, get_provider_appointments, get_provider_prescription_requests
)

logger = logging.getLogger(__name__)

# Base repository with common functionality
class BaseRepository:
    """Base repository with common CRUD operations."""
    
    @classmethod
    def _log_operation(cls, operation, entity_type, entity_id=None, error=None):
        """Log operations for debugging."""
        if error:
            logger.error(f"{operation} {entity_type} {entity_id if entity_id else ''} failed: {error}")
        else:
            logger.debug(f"{operation} {entity_type} {entity_id if entity_id else ''} successful")

    @classmethod
    def get_by_id(cls, entity_id):
        """Base method to get entity by ID."""
        try:
            # This would be overridden by child classes
            return None
        except Exception as e:
            cls._log_operation("get", cls.__name__, entity_id, str(e))
            return None
    
    @classmethod
    def create(cls, data):
        """Base method to create entity."""
        try:
            # This would be overridden by child classes
            return None
        except Exception as e:
            cls._log_operation("create", cls.__name__, None, str(e))
            return None
    
    @classmethod
    def update(cls, entity_id, data):
        """Base method to update entity."""
        try:
            # This would be overridden by child classes
            return None
        except Exception as e:
            cls._log_operation("update", cls.__name__, entity_id, str(e))
            return None
    
    @classmethod
    def delete(cls, entity_id):
        """Base method to delete entity."""
        try:
            # This would be overridden by child classes
            return False
        except Exception as e:
            cls._log_operation("delete", cls.__name__, entity_id, str(e))
            return False


class PatientRepository(BaseRepository):
    """Repository for patient-related operations."""
    
    @classmethod
    def get_current(cls, request):
        """Get the current patient based on session or auth."""
        try:
            return get_current_patient(request)
        except Exception as e:
            cls._log_operation("get_current", "Patient", None, str(e))
            # Return default patient as fallback
            return {
                'id': 1,
                'first_name': 'Default',
                'last_name': 'User',
                'email': 'default@example.com',
                'date_of_birth': '2000-01-01',
                'ohip_number': '0000000000',
                'primary_phone': '(000) 000-0000'
            }
    
    @classmethod
    def get_by_id(cls, patient_id):
        """Get a patient by ID."""
#        try:
#            print (f"Fetching patient with ID: {patient_id}")  # Debug
#            return get_patient_by_id(patient_id)
#        except Exception as e:
#            cls._log_operation("get", "Patient", patient_id, str(e))
#            return None
        """Get a patient by ID."""
        try:
            print(f"[REPOSITORY] Fetching patient with ID: {patient_id}, type: {type(patient_id)}")
            patient = get_patient_by_id(patient_id)
            print(f"[REPOSITORY] Retrieved: {patient.get('first_name')} {patient.get('last_name')}, ID: {patient.get('id')}")
            return patient
        except Exception as e:
            cls._log_operation("get", "Patient", patient_id, str(e))
            print(f"[REPOSITORY] Error: {str(e)}")
            return None

    @classmethod
    def get_all(cls):
        """Get all patients."""
        try:
            return get_all_patients()
        except Exception as e:
            cls._log_operation("get_all", "Patient", None, str(e))
            return []
    
    @classmethod
    def create(cls, data):
        """Create a new patient."""
        try:
            # In mock mode, simply return the data with an ID
            # In real DB mode, this would create a Patient record
            patient_data = data.copy()
            patient_data['id'] = len(get_all_patients()) + 1
            return patient_data
        except Exception as e:
            cls._log_operation("create", "Patient", None, str(e))
            return None
    
    @classmethod
    def update(cls, patient_id, data):
        """Update a patient."""
        try:
            # Get the current patient data
            patient = get_patient_by_id(patient_id)
            if not patient:
                return None
            
            # Update the patient data
            updated_patient = {**patient, **data}
            
            # In a real DB, this would save changes
            
            return updated_patient
        except Exception as e:
            cls._log_operation("update", "Patient", patient_id, str(e))
            return None
    
    @classmethod
    def search(cls, patient_id, query):
        """Search patient records."""
        try:
            return search_patient_data(query, patient_id)
        except Exception as e:
            cls._log_operation("search", "Patient", patient_id, str(e))
            return {
                'prescriptions': [],
                'appointments': [],
                'messages': []
            }


class PrescriptionRepository(BaseRepository):
    """Repository for prescription-related operations."""
    
    @classmethod
    def get_by_id(cls, prescription_id):
        """Get a prescription by ID."""
        try:
            return get_prescription_by_id(prescription_id)
        except Exception as e:
            cls._log_operation("get", "Prescription", prescription_id, str(e))
            return None
    
    @classmethod
    def get_all(cls):
        """Get all prescriptions."""
        try:
            return get_all_prescriptions()
        except Exception as e:
            cls._log_operation("get_all", "Prescription", None, str(e))
            return []
    
    @classmethod
    def get_active_for_patient(cls, patient_id):
        """Get active prescriptions for a patient."""
        try:
            prescriptions = get_patient_prescriptions(patient_id)
            return [p for p in prescriptions if p.get('status') in ['Active', 'Renewal Soon']]
        except Exception as e:
            cls._log_operation("get_active", "Prescription", patient_id, str(e))
            return []
    
    @classmethod
    def get_historical_for_patient(cls, patient_id):
        """Get historical prescriptions for a patient."""
        try:
            prescriptions = get_patient_prescriptions(patient_id)
            return [p for p in prescriptions if p.get('status') not in ['Active', 'Renewal Soon']]
        except Exception as e:
            cls._log_operation("get_historical", "Prescription", patient_id, str(e))
            return []
    
    @classmethod
    def get_by_date_range(cls, provider_id, start_date, end_date):
        """Get prescriptions within a date range for a provider.
        
        Args:
            provider_id: The ID of the provider
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            list: List of prescriptions within the date range
        """
        try:
            # In a real implementation, this would query the database with a date filter
            # For the mock implementation, we'll filter the in-memory data
            
            # Get all prescriptions
            all_prescriptions = get_all_prescriptions()
            
            # Convert date strings to datetime objects for comparison
            from datetime import datetime
            
            filtered_prescriptions = []
            for prescription in all_prescriptions:
                # In a real implementation, this would be handled by the database query
                if 'prescribed_date' in prescription:
                    try:
                        # Try different date formats
                        formats = ['%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']
                        prescription_date = None
                        
                        for fmt in formats:
                            try:
                                prescription_date = datetime.strptime(prescription['prescribed_date'], fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if prescription_date and start_date <= prescription_date <= end_date:
                            filtered_prescriptions.append(prescription)
                    except (ValueError, TypeError) as e:
                        # Skip prescriptions with invalid dates
                        cls._log_operation("date_parse", "Prescription", prescription.get('id'), str(e))
            
            return filtered_prescriptions
        except Exception as e:
            cls._log_operation("get_by_date_range", "Prescription", provider_id, str(e))
            return []
    
    @classmethod
    def get_active_count(cls):
        """Get count of active prescriptions."""
        try:
            prescriptions = get_all_prescriptions()
            return len([p for p in prescriptions if p.get('status') in ['Active', 'Renewal Soon']])
        except Exception as e:
            cls._log_operation("get_active_count", "Prescription", None, str(e))
            return 0
    
    @classmethod
    def get_refill_request_count(cls):
        """Get count of pending refill requests."""
        try:
            # In a real implementation, this would query the database
            # For the mock implementation, we'll return a fixed number
            prescriptions = get_all_prescriptions()
            return len([p for p in prescriptions if p.get('status') == 'Renewal Requested'])
        except Exception as e:
            cls._log_operation("get_refill_request_count", "Prescription", None, str(e))
            return 0
    
    @classmethod
    def create(cls, data):
        """Create a new prescription."""
        try:
            return save_prescription_request(data)
        except Exception as e:
            cls._log_operation("create", "Prescription", None, str(e))
            return None
    
    @classmethod
    def update(cls, prescription_id, data):
        """Update a prescription."""
        try:
            # Get the current prescription data
            prescription = get_prescription_by_id(prescription_id)
            if not prescription:
                return None
            
            # Update the prescription data
            updated_prescription = {**prescription, **data}
            
            # In a real DB, this would save changes
            
            return updated_prescription
        except Exception as e:
            cls._log_operation("update", "Prescription", prescription_id, str(e))
            return None
    
    @classmethod
    def approve_prescription(cls, prescription_id):
        """Approve a prescription renewal/request."""
        try:
            # Get the current prescription
            prescription = get_prescription_by_id(prescription_id)
            if not prescription:
                return False
            
            # Update the prescription status
            updated_prescription = {**prescription, 'status': 'Active'}
            
            # In a real DB, this would save changes
            
            return True
        except Exception as e:
            cls._log_operation("approve", "Prescription", prescription_id, str(e))
            return False
        

class AppointmentRepository(BaseRepository):
    """Repository for appointment-related operations."""
    
    @classmethod
    def get_by_id(cls, appointment_id):
        """Get an appointment by ID."""
        try:
            return get_appointment_by_id(appointment_id)
        except Exception as e:
            cls._log_operation("get", "Appointment", appointment_id, str(e))
            return None
    
    @classmethod
    def get_all(cls):
        """Get all appointments."""
        try:
            return get_all_appointments()
        except Exception as e:
            cls._log_operation("get_all", "Appointment", None, str(e))
            return []
    
    @classmethod
    def get_upcoming_for_patient(cls, patient_id):
        """Get upcoming appointments for a patient."""
        try:
            appointments = get_patient_appointments(patient_id)
            
            # In a real implementation, would filter by date
            # For mock data, include appointments without "Completed" status
            return [a for a in appointments if a.get('status') != 'Completed']
        except Exception as e:
            cls._log_operation("get_upcoming", "Appointment", patient_id, str(e))
            return []
    
    @classmethod
    def get_past_for_patient(cls, patient_id):
        """Get past appointments for a patient."""
        try:
            appointments = get_patient_appointments(patient_id)
            
            # In a real implementation, would filter by date
            # For mock data, include appointments with "Completed" status
            return [a for a in appointments if a.get('status') == 'Completed']
        except Exception as e:
            cls._log_operation("get_past", "Appointment", patient_id, str(e))
            return []
    
    @classmethod
    def create(cls, data):
        """Create a new appointment."""
        try:
            # In mock mode, create an appointment with an ID
            appointment_data = data.copy()
            appointment_data['id'] = len(get_all_appointments()) + 1
            return appointment_data
        except Exception as e:
            cls._log_operation("create", "Appointment", None, str(e))
            return None
    
    @classmethod
    def update(cls, appointment_id, data):
        """Update an appointment."""
        try:
            # Get the current appointment data
            appointment = get_appointment_by_id(appointment_id)
            if not appointment:
                return None
            
            # Update the appointment data
            updated_appointment = {**appointment, **data}
            
            # In a real DB, this would save changes
            
            return updated_appointment
        except Exception as e:
            cls._log_operation("update", "Appointment", appointment_id, str(e))
            return None


class MessageRepository(BaseRepository):
    """Repository for message-related operations."""
    
    @classmethod
    def get_by_id(cls, message_id):
        """Get a message by ID."""
        try:
            return get_message_by_id(message_id)
        except Exception as e:
            cls._log_operation("get", "Message", message_id, str(e))
            return None
    
    @classmethod
    def get_all(cls):
        """Get all messages."""
        try:
            return get_all_messages()
        except Exception as e:
            cls._log_operation("get_all", "Message", None, str(e))
            return []
    
    @classmethod
    def get_unread_for_patient(cls, patient_id):
        """Get unread messages for a patient."""
        try:
            messages = get_patient_messages(patient_id)
            return [m for m in messages if not m.get('read', False)]
        except Exception as e:
            cls._log_operation("get_unread", "Message", patient_id, str(e))
            return []
    
    @classmethod
    def get_read_for_patient(cls, patient_id):
        """Get read messages for a patient."""
        try:
            messages = get_patient_messages(patient_id)
            return [m for m in messages if m.get('read', False)]
        except Exception as e:
            cls._log_operation("get_read", "Message", patient_id, str(e))
            return []
    
    @classmethod
    def create(cls, data):
        """Create a new message."""
        try:
            # In mock mode, create a message with an ID
            message_data = data.copy()
            message_data['id'] = len(get_all_messages()) + 1
            message_data['timestamp'] = datetime.now().strftime('Today, %I:%M %p')
            message_data['read'] = False
            return message_data
        except Exception as e:
            cls._log_operation("create", "Message", None, str(e))
            return None
    
    @classmethod
    def update(cls, message_id, data):
        """Update a message."""
        try:
            # Get the current message data
            message = get_message_by_id(message_id)
            if not message:
                return None
            
            # Update the message data
            updated_message = {**message, **data}
            
            # In a real DB, this would save changes
            
            return updated_message
        except Exception as e:
            cls._log_operation("update", "Message", message_id, str(e))
            return None
# Add to repositories.py

class ProviderRepository(BaseRepository):
    """Repository for provider-related operations."""
    
    @classmethod
    def get_current(cls, request):
        """Get the current provider based on session or auth."""
        try:
            return get_current_provider(request)
        except Exception as e:
            cls._log_operation("get_current", "Provider", None, str(e))
            # Return default provider as fallback
            return {
                'id': 1,
                'first_name': 'James',
                'last_name': 'Smith',
                'title': 'Dr.',
                'specialty': 'Family Medicine',
                'email': 'dr.smith@northernhealth.example.com',
                'phone': '(555) 987-6543',
                'license_number': 'MD12345'
            }
    
    @classmethod
    def get_by_id(cls, provider_id):
        """Get a provider by ID."""
        try:
            return get_provider_by_id(provider_id)
        except Exception as e:
            cls._log_operation("get", "Provider", provider_id, str(e))
            return None

    @classmethod
    def get_patients(cls, provider_id):
        """Get all patients for a provider with additional fields for the dashboard."""
        try:
            patients = get_provider_patients(provider_id)
            
            # Add some derived fields to patients
            enriched_patients = []
            
            for patient in patients:
                # Calculate age (would normally come from DB)
                if 'date_of_birth' in patient:
                    try:
                        dob = datetime.strptime(patient['date_of_birth'], '%Y-%m-%d').date()
                        today = datetime.now().date()
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                        patient['age'] = age
                    except (ValueError, TypeError):
                        patient['age'] = None
                
                # Add gender if not present (mock data)
                if 'gender' not in patient:
                    patient['gender'] = 'Female' if patient.get('first_name', '').endswith('a') or patient.get('first_name', '').endswith('y') else 'Male'  
                
                # Add status for UI (would come from DB in real app)
                if 'status' not in patient:
                    if patient.get('id') % 3 == 0:  # Just for demo variety
                        patient['status'] = 'Follow-up Needed'
                    elif patient.get('id') % 7 == 0:
                        patient['status'] = 'Critical Review'
                    else:
                        patient['status'] = 'Stable'
                
                # Add last_visit_reason if not present
                if 'last_visit_reason' not in patient and 'last_visit' in patient:
                    reasons = ['Annual Checkup', 'Prescription Review', 'Blood Work Results', 'Follow-up', 'Consultation']
                    patient['last_visit_reason'] = reasons[patient.get('id', 0) % len(reasons)]
                
                # Flag patients that require attention
                if patient.get('status') in ['Critical Review', 'Follow-up Needed']:
                    patient['requires_attention'] = True
                
                enriched_patients.append(patient)
            
            return enriched_patients
        except Exception as e:
            cls._log_operation("get_patients", "Provider", provider_id, str(e))
            # Return empty list as fallback
            return []


    @classmethod
    def get_appointments(cls, provider_id, date=None):
        """Get appointments for a provider, optionally filtered by date."""
        try:
            appointments = get_provider_appointments(provider_id)
            if date:
                # Filter by date if provided - in a real implementation
                # this would be handled by the database query
                pass
            return appointments
        except Exception as e:
            cls._log_operation("get_appointments", "Provider", provider_id, str(e))
            return []
    
    @classmethod
    def get_prescription_requests(cls, provider_id):
        """Get pending prescription requests for a provider."""
        try:
            return get_provider_prescription_requests(provider_id)
        except Exception as e:
            cls._log_operation("get_prescription_requests", "Provider", provider_id, str(e))
            return []
