# data_access.py

from django.conf import settings
from datetime import datetime, timedelta
import uuid

# Default setting for using mock data
USE_MOCK_DATA = getattr(settings, 'USE_MOCK_DATA', True)

# ===== PATIENT DATA ACCESS =====

def get_patient_by_id(patient_id, use_mock=USE_MOCK_DATA):
    """Get a patient by ID."""
    print(f"[DATA_ACCESS] get_patient_by_id called with ID: {patient_id}, type: {type(patient_id)}")
    
    # Convert to integer if it's a string
    if isinstance(patient_id, str) and patient_id.isdigit():
        patient_id = int(patient_id)

    if use_mock:
        # Mock patient data
        all_patients= [
            {
                'id': 1,
                'first_name': 'Jane',
                'last_name': 'Doe',
                'email': 'jane.doe@example.com',
                'date_of_birth': '1985-04-12',
                'ohip_number': '1234567890',
                'primary_phone': '(555) 123-4567',
                'alternate_phone': '(555) 987-6543',
                'address': '123 Health St, Toronto, ON',
                'virtual_care_consent': True,
                'ehr_consent': True
            },
            {
                'id': 2,
                'first_name': 'John',
                'last_name': 'Smith',
                'email': 'john.smith@example.com',
                'date_of_birth': '1978-08-23',
                'ohip_number': '2345678901',
                'primary_phone': '(555) 234-5678',
                'alternate_phone': '',
                'address': '456 Main St, Toronto, ON',
                'virtual_care_consent': True,
                'ehr_consent': True,
                'current_medications': 'Metformin 500mg twice daily',
                'allergies': 'None',
                'emergency_contact_name': 'Sarah Smith',
                'emergency_contact_phone': '(555) 234-5678',
                'last_visit': 'February 28, 2025',
                'last_visit_reason': 'Blood Work Results',
                'status': 'Follow-up Needed'
            },
            {
                'id': 3,
                'first_name': 'Robert',
                'last_name': 'Johnson',
                'email': 'robert.johnson@example.com',
                'date_of_birth': '1990-11-15',
                'ohip_number': '3456789012',
                'primary_phone': '(555) 345-6789',
                'alternate_phone': '',
                'address': '789 Oak St, Toronto, ON',
                'virtual_care_consent': True,
                'ehr_consent': True,
                'current_medications': 'Atorvastatin 20mg daily',
                'allergies': 'Sulfa drugs',
                'emergency_contact_name': 'Lisa Johnson',
                'emergency_contact_phone': '(555) 345-6789',
                'last_visit': 'March 1, 2025',
                'last_visit_reason': 'Prescription Review',
                'status': 'Critical Review'
            },
            {
                'id': 4,
                'first_name': 'Emily',
                'last_name': 'Williams',
                'email': 'emily.williams@example.com',
                'date_of_birth': '1982-05-30',
                'ohip_number': '4567890123',
                'primary_phone': '(555) 456-7890',
                'alternate_phone': '(555) 567-8901',
                'address': '321 Elm St, Toronto, ON',
                'virtual_care_consent': True,
                'ehr_consent': True,
                'current_medications': 'None',
                'allergies': 'Peanuts',
                'emergency_contact_name': 'Michael Williams',
                'emergency_contact_phone': '(555) 456-7890',
                'last_visit': 'January 20, 2025',
                'last_visit_reason': 'Annual Checkup',
                'status': 'Stable'
            }
        ]
        # Find the patient with matching ID
        for patient in all_patients:
            if patient['id'] == patient_id:
                print(f"[DATA_ACCESS] Found matching patient: {patient['first_name']} {patient['last_name']}")
                return patient
 
        # If no matching ID is found, return the first patient (fallback)
        print(f"[DATA_ACCESS] No matching patient found for ID: {patient_id}. Types - ID: {type(patient_id)}, Patient ID example: {type(all_patients[0]['id'])}")
        
        # Return first patient as fallback
        print(f"[DATA_ACCESS] Returning fallback patient: {all_patients[0]['first_name']} {all_patients[0]['last_name']}")
        return all_patients[0]

    else:
        # When connected to DB:
        # from .models import PatientRegistration
        # return PatientRegistration.objects.get(id=patient_id)
        pass

def get_current_patient(request, use_mock=USE_MOCK_DATA):
    """Get the current patient based on session or auth."""
    # In the future, get from request.user
    # For now, use a fixed patient ID from session or default to 1
    patient_id = request.session.get('mock_patient_id', 1)
    return get_patient_by_id(patient_id, use_mock)

# ===== PRESCRIPTION DATA ACCESS =====

def get_prescription_by_id(prescription_id, use_mock=USE_MOCK_DATA):
    """Get a prescription by ID."""
    if use_mock:
        mock_prescriptions = get_all_prescriptions(use_mock=True)
        for prescription in mock_prescriptions:
            if prescription['id'] == prescription_id:
                return prescription
        return None
    else:
        # When connected to DB:
        # from .models import Prescription
        # return Prescription.objects.get(id=prescription_id)
        pass

def get_patient_prescriptions(patient_id, use_mock=USE_MOCK_DATA):
    """Get all prescriptions for a patient."""
    if use_mock:
        # All mock prescriptions are for the same patient for now
        return get_all_prescriptions(use_mock=True)
    else:
        # When connected to DB:
        # from .models import Prescription
        # return Prescription.objects.filter(patient_id=patient_id)
        pass

def get_all_prescriptions(use_mock=USE_MOCK_DATA):
    """Get all prescriptions."""
    if use_mock:
        today = datetime.now().date()
        return [
            {
                'id': 1,
                'medication_name': 'Amoxicillin',
                'dosage': '500mg, 3 times daily for 10 days',
                'prescribed_by': 'Dr. Johnson',
                'prescribed_date': 'March 25, 2025',
                'refills_remaining': 0,
                'status': 'Active',
                'instructions': 'Take one tablet by mouth three times daily for 10 days',
                'side_effects': 'Diarrhea, nausea, vomiting, rash',
                'warnings': 'May cause allergic reaction in patients with penicillin allergy',
                'expires': 'April 15, 2025',
                'pharmacy': 'Northern Pharmacy'
            },
            {
                'id': 2,
                'medication_name': 'Lisinopril',
                'dosage': '10mg, once daily',
                'prescribed_by': 'Dr. Smith',
                'prescribed_date': 'January 10, 2025',
                'refills_remaining': 1,
                'status': 'Renewal Soon',
                'instructions': 'Take one tablet by mouth once daily in the morning',
                'side_effects': 'Dry cough, dizziness, headache',
                'warnings': 'Monitor blood pressure regularly',
                'expires': 'April 5, 2025',
                'pharmacy': 'Northern Pharmacy'
            },
            {
                'id': 3,
                'medication_name': 'Metformin',
                'dosage': '500mg, twice daily with meals',
                'prescribed_by': 'Dr. Johnson',
                'prescribed_date': 'February 18, 2025',
                'refills_remaining': 2,
                'status': 'Active',
                'instructions': 'Take one tablet by mouth twice daily with meals',
                'side_effects': 'Nausea, diarrhea, decreased appetite',
                'warnings': 'Report unusual symptoms to your doctor',
                'expires': 'May 15, 2025',
                'pharmacy': 'Northern Pharmacy'
            }
        ]
    else:
        # When connected to DB:
        # from .models import Prescription
        # return Prescription.objects.all()
        pass

def save_prescription_request(prescription_data, use_mock=USE_MOCK_DATA):
    """Save a new prescription request."""
    if use_mock:
        # Generate a unique ID for the mock prescription
        new_id = len(get_all_prescriptions(use_mock=True)) + 1
        
        # Add the prescription to session if needed
        # This isn't ideal long-term but works for mock data
        prescription_data['id'] = new_id
        return prescription_data
    else:
        # When connected to DB:
        # from .models import PrescriptionRequest
        # prescription = PrescriptionRequest(**prescription_data)
        # prescription.save()
        # return prescription
        pass

# ===== APPOINTMENT DATA ACCESS =====

def get_appointment_by_id(appointment_id, use_mock=USE_MOCK_DATA):
    """Get an appointment by ID."""
    if use_mock:
        mock_appointments = get_all_appointments(use_mock=True)
        for appointment in mock_appointments:
            if appointment['id'] == appointment_id:
                return appointment
        return None
    else:
        # When connected to DB:
        # from .models import Appointment
        # return Appointment.objects.get(id=appointment_id)
        pass

def get_patient_appointments(patient_id, use_mock=USE_MOCK_DATA):
    """Get all appointments for a patient."""
    if use_mock:
        # All mock appointments are for the same patient for now
        return get_all_appointments(use_mock=True)
    else:
        # When connected to DB:
        # from .models import Appointment
        # return Appointment.objects.filter(patient_id=patient_id)
        pass

def get_all_appointments(use_mock=USE_MOCK_DATA):
    """Get all appointments."""
    if use_mock:
        return [
            {
                'id': 1,
                'doctor': 'Dr. Johnson',
                'time': 'Apr 3, 2025 - 10:00 AM',
                'type': 'In-Person',
                'reason': 'Annual checkup',
                'location': 'Northern Health Clinic, Room 305',
                'notes': 'Annual physical examination'
            },
            {
                'id': 2,
                'doctor': 'Dr. Smith',
                'time': 'Apr 10, 2025 - 2:30 PM',
                'type': 'Virtual',
                'reason': 'Follow-up',
                'location': 'Jitsi Video',
                'notes': 'Medication review and blood pressure check'
            },
            {
                'id': 3,
                'doctor': 'Dr. Wilson',
                'time': 'Mar 15, 2025 - 11:30 AM',
                'type': 'Virtual',
                'reason': 'Prescription Review',
                'location': 'Jitsi Video',
                'notes': 'Review current medications',
                'status': 'Completed'
            },
            {
                'id': 4,
                'doctor': 'Dr. Johnson',
                'time': 'Feb 28, 2025 - 3:00 PM',
                'type': 'In-Person',
                'reason': 'Blood Work Results',
                'location': 'Northern Health Clinic, Room 210',
                'notes': 'Review blood work results',
                'status': 'Completed'
            }
        ]
    else:
        # When connected to DB:
        # from .models import Appointment
        # return Appointment.objects.all()
        pass

# ===== MESSAGE DATA ACCESS =====

def get_message_by_id(message_id, use_mock=USE_MOCK_DATA):
    """Get a message by ID."""
    if use_mock:
        mock_messages = get_all_messages(use_mock=True)
        for message in mock_messages:
            if message['id'] == message_id:
                return message
        return None
    else:
        # When connected to DB:
        # from .models import Message
        # return Message.objects.get(id=message_id)
        pass

def get_patient_messages(patient_id, use_mock=USE_MOCK_DATA):
    """Get all messages for a patient."""
    if use_mock:
        # All mock messages are for the same patient for now
        return get_all_messages(use_mock=True)
    else:
        # When connected to DB:
        # from .models import Message
        # return Message.objects.filter(recipient_id=patient_id)
        pass

def get_all_messages(use_mock=USE_MOCK_DATA):
    """Get all messages."""
    if use_mock:
        return [
            {
                'id': 1,
                'sender': 'Dr. Johnson',
                'content': 'Your recent blood work looks good. All values are within normal ranges. We should discuss your medication regimen at your next appointment.',
                'timestamp': 'Today, 10:30 AM',
                'read': False
            },
            {
                'id': 2,
                'sender': 'Nurse Williams',
                'content': 'This is a confirmation for your upcoming appointment with Dr. Smith on April 10, 2025 at 2:30 PM. Please arrive 15 minutes early to complete any necessary paperwork.',
                'timestamp': 'Yesterday',
                'read': False
            },
            {
                'id': 3,
                'sender': 'Dr. Wilson',
                'content': "I've renewed your prescription for Lisinopril. The new prescription has been sent to Northern Pharmacy. You can pick it up starting tomorrow.",
                'timestamp': 'Mar 25',
                'read': True
            },
            {
                'id': 4,
                'sender': 'Lab Services',
                'content': 'Your recent laboratory test results are now available for review. Your healthcare provider has been notified and will contact you to discuss the results.',
                'timestamp': 'Mar 22',
                'read': True
            },
            {
                'id': 5,
                'sender': 'Billing Department',
                'content': 'Thank you for providing your updated insurance information. We have processed the changes and updated your account. Your next appointment will be billed to your new insurance provider.',
                'timestamp': 'Mar 18',
                'read': True
            }
        ]
    else:
        # When connected to DB:
        # from .models import Message
        # return Message.objects.all()
        pass

# ===== SEARCH FUNCTIONALITY =====

def search_patient_data(query, patient_id=None, use_mock=USE_MOCK_DATA):
    """Search across patient data (prescriptions, appointments, messages)."""
    if use_mock:
        results = {
            'prescriptions': [],
            'appointments': [],
            'messages': []
        }
        
        # Get data for patient
        prescriptions = get_patient_prescriptions(patient_id, use_mock=True)
        appointments = get_patient_appointments(patient_id, use_mock=True)
        messages = get_patient_messages(patient_id, use_mock=True)
        
        # Filter by query
        query = query.lower()
        for prescription in prescriptions:
            if (query in prescription['medication_name'].lower() or 
                query in prescription['prescribed_by'].lower() or
                query in prescription['instructions'].lower()):
                results['prescriptions'].append(prescription)
                
        for appointment in appointments:
            if (query in appointment['doctor'].lower() or 
                query in appointment['reason'].lower() or
                query in appointment['notes'].lower()):
                results['appointments'].append(appointment)
                
        for message in messages:
            if (query in message['sender'].lower() or 
                query in message['content'].lower()):
                results['messages'].append(message)
                
        return results
    else:
        # When connected to DB, implement real search
        pass

# ===== PROVIDER DATA ACCESS =========================================================================================================

def get_provider_by_id(provider_id, use_mock=USE_MOCK_DATA):
    """Get a provider by ID."""
    if use_mock:
        # Mock provider data
        return {
            'id': provider_id,
            'first_name': 'James',
            'last_name': 'Smith',
            'title': 'Dr.',
            'specialty': 'Family Medicine',
            'email': 'dr.smith@northernhealth.example.com',
            'phone': '(555) 987-6543',
            'license_number': 'MD12345',
            'profile_image': None
        }
    else:
        # When connected to DB:
        # from .models import Provider
        # return Provider.objects.get(id=provider_id)
        pass

def get_current_provider(request, use_mock=USE_MOCK_DATA):
    """Get the current provider based on session or auth."""
    # In the future, get from request.user
    # For now, use a fixed provider ID from session or default to 1
    provider_id = request.session.get('mock_provider_id', 1)
    return get_provider_by_id(provider_id, use_mock)

def get_provider_patients(provider_id, use_mock=USE_MOCK_DATA):
    """Get all patients for a provider."""
    if use_mock:
        return [
            {
                'id': 1,
                'first_name': 'Jane',
                'last_name': 'Doe',
                'date_of_birth': '1985-04-12',
                'email': 'jane.doe@example.com',
                'phone': '(555) 123-4567',
                'ohip_number': '1234567890',
                'last_visit': 'March 15, 2025',
                'upcoming_appointment': 'April 3, 2025'
            },
            {
                'id': 2,
                'first_name': 'John',
                'last_name': 'Smith',
                'date_of_birth': '1978-08-23',
                'email': 'john.smith@example.com',
                'phone': '(555) 234-5678',
                'ohip_number': '2345678901',
                'last_visit': 'February 28, 2025',
                'upcoming_appointment': 'April 10, 2025'
            },
            {
                'id': 3,
                'first_name': 'Robert',
                'last_name': 'Johnson',
                'date_of_birth': '1990-11-15',
                'email': 'robert.johnson@example.com',
                'phone': '(555) 345-6789',
                'ohip_number': '3456789012',
                'last_visit': 'March 1, 2025',
                'upcoming_appointment': None
            },
            {
                'id': 4,
                'first_name': 'Emily',
                'last_name': 'Williams',
                'date_of_birth': '1982-05-30',
                'email': 'emily.williams@example.com',
                'phone': '(555) 456-7890',
                'ohip_number': '4567890123',
                'last_visit': 'January 20, 2025',
                'upcoming_appointment': 'April 5, 2025'
            }
        ]
    else:
        # When connected to DB:
        # from .models import Patient
        # return Patient.objects.filter(provider_id=provider_id)
        pass

def get_provider_appointments(provider_id, use_mock=USE_MOCK_DATA):
    """Get all appointments for a provider."""
    if use_mock:
        return [
            {
                'id': 1,
                'patient_name': 'Jane Doe',
                'patient_id': 1,
                'time': 'Apr 3, 2025 - 10:00 AM',
                'type': 'In-Person',
                'reason': 'Annual checkup',
                'location': 'Northern Health Clinic, Room 305',
                'notes': 'Annual physical examination'
            },
            {
                'id': 2,
                'patient_name': 'John Smith',
                'patient_id': 2,
                'time': 'Apr 10, 2025 - 2:30 PM',
                'type': 'Virtual',
                'reason': 'Follow-up',
                'location': 'Jitsi Video',
                'notes': 'Medication review and blood pressure check'
            },
            {
                'id': 3,
                'patient_name': 'Emily Williams',
                'patient_id': 4,
                'time': 'Apr 5, 2025 - 11:30 AM',
                'type': 'In-Person',
                'reason': 'New patient visit',
                'location': 'Northern Health Clinic, Room 201',
                'notes': 'Initial consultation'
            }
        ]
    else:
        # When connected to DB:
        # from .models import Appointment
        # return Appointment.objects.filter(provider_id=provider_id)
        pass

def get_provider_prescription_requests(provider_id, use_mock=USE_MOCK_DATA):
    """Get all prescription requests for a provider."""
    if use_mock:
        return [
            {
                'id': 1,
                'patient_name': 'Jane Doe',
                'patient_id': 1,
                'medication_name': 'Lisinopril',
                'current_dosage': '10mg, once daily',
                'requested_date': 'April 1, 2025',
                'status': 'Pending',
                'expires': 'April 15, 2025'  # Added expiration date
            },
            {
                'id': 2,
                'patient_name': 'John Smith',
                'patient_id': 2,
                'medication_name': 'Metformin',
                'current_dosage': '500mg, twice daily',
                'requested_date': 'March 30, 2025',
                'status': 'Pending',
                'expires': 'April 10, 2025'  # Added expiration date
            }
        ]
    else:
        # When connected to DB:
        # from .models import PrescriptionRequest
        # return PrescriptionRequest.objects.filter(provider_id=provider_id)
        pass

def get_provider_patient_records(provider_id, patient_id, use_mock=USE_MOCK_DATA):
    """Get patient records for a specific patient (provider view)."""
    if use_mock:
        return {
            'medical_history': [
                {
                    'date': 'March 15, 2025',
                    'condition': 'Hypertension',
                    'notes': 'Diagnosed with stage 1 hypertension. Started on Lisinopril 10mg daily.'
                },
                {
                    'date': 'January 10, 2025',
                    'condition': 'Upper Respiratory Infection',
                    'notes': 'Symptoms include cough, congestion, and low-grade fever. Prescribed Amoxicillin.'
                }
            ],
            'allergies': ['Penicillin', 'Pollen'],
            'medications': [
                {
                    'name': 'Lisinopril',
                    'dosage': '10mg',
                    'frequency': 'Once daily',
                    'start_date': 'March 15, 2025'
                },
                {
                    'name': 'Metformin',
                    'dosage': '500mg',
                    'frequency': 'Twice daily',
                    'start_date': 'February 18, 2025'
                }
            ],
            'lab_results': [
                {
                    'date': 'March 10, 2025',
                    'test': 'Complete Blood Count',
                    'result': 'Normal',
                    'notes': 'All values within normal range.'
                },
                {
                    'date': 'March 10, 2025',
                    'test': 'Blood Pressure',
                    'result': '140/90 mmHg',
                    'notes': 'Elevated. Recommended lifestyle changes and medication.'
                }
            ]
        }
    else:
        # When connected to DB, retrieve actual patient records
        pass

# ===== ADMIN DASHBOARD DATA ACCESS =====

def get_admin_by_id(admin_id, use_mock=USE_MOCK_DATA):
    """Get an admin user by ID."""
    if use_mock:
        # Mock admin data
        return {
            'id': admin_id,
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@northernhealth.example.com',
            'is_superuser': True
        }
    else:
        # When connected to DB:
        # from django.contrib.auth.models import User
        # return User.objects.get(id=admin_id, is_superuser=True)
        pass

def get_current_admin(request, use_mock=USE_MOCK_DATA):
    """Get the current admin based on session or auth."""
    # In the future, get from request.user
    # For now, use a fixed admin ID from session or default to 1
    admin_id = request.session.get('mock_admin_id', 1)
    return get_admin_by_id(admin_id, use_mock)

def get_all_patients(use_mock=USE_MOCK_DATA):
    """Get all patients (admin view)."""
    if use_mock:
        return [
            {
                'id': 1,
                'first_name': 'Jane',
                'last_name': 'Doe',
                'date_of_birth': '1985-04-12',
                'email': 'jane.doe@example.com',
                'phone': '(555) 123-4567',
                'ohip_number': '1234567890',
                'provider': 'Dr. James Smith',
                'registration_date': 'January 5, 2025',
                'last_visit': 'March 15, 2025',
                'upcoming_appointment': 'April 3, 2025'
            },
            {
                'id': 2,
                'first_name': 'John',
                'last_name': 'Smith',
                'date_of_birth': '1978-08-23',
                'email': 'john.smith@example.com',
                'phone': '(555) 234-5678',
                'ohip_number': '2345678901',
                'provider': 'Dr. James Smith',
                'registration_date': 'February 10, 2025',
                'last_visit': 'February 28, 2025',
                'upcoming_appointment': 'April 10, 2025'
            },
            {
                'id': 3,
                'first_name': 'Robert',
                'last_name': 'Johnson',
                'date_of_birth': '1990-11-15',
                'email': 'robert.johnson@example.com',
                'phone': '(555) 345-6789',
                'ohip_number': '3456789012',
                'provider': 'Dr. Sarah Lee',
                'registration_date': 'December 15, 2024',
                'last_visit': 'March 1, 2025',
                'upcoming_appointment': None
            },
            {
                'id': 4,
                'first_name': 'Emily',
                'last_name': 'Williams',
                'date_of_birth': '1982-05-30',
                'email': 'emily.williams@example.com',
                'phone': '(555) 456-7890',
                'ohip_number': '4567890123',
                'provider': 'Dr. Michael Wilson',
                'registration_date': 'March 1, 2025',
                'last_visit': 'January 20, 2025',
                'upcoming_appointment': 'April 5, 2025'
            }
        ]
    else:
        # When connected to DB:
        # from .models import PatientRegistration
        # return PatientRegistration.objects.all()
        pass

def get_all_providers(use_mock=USE_MOCK_DATA):
    """Get all providers (admin view)."""
    if use_mock:
        return [
            {
                'id': 1,
                'first_name': 'James',
                'last_name': 'Smith',
                'title': 'Dr.',
                'specialty': 'Family Medicine',
                'email': 'dr.smith@northernhealth.example.com',
                'phone': '(555) 987-6543',
                'license_number': 'MD12345',
                'patient_count': 15,
                'join_date': 'January 1, 2025'
            },
            {
                'id': 2,
                'first_name': 'Sarah',
                'last_name': 'Lee',
                'title': 'Dr.',
                'specialty': 'Pediatrics',
                'email': 'dr.lee@northernhealth.example.com',
                'phone': '(555) 876-5432',
                'license_number': 'MD23456',
                'patient_count': 22,
                'join_date': 'January 1, 2025'
            },
            {
                'id': 3,
                'first_name': 'Michael',
                'last_name': 'Wilson',
                'title': 'Dr.',
                'specialty': 'Cardiology',
                'email': 'dr.wilson@northernhealth.example.com',
                'phone': '(555) 765-4321',
                'license_number': 'MD34567',
                'patient_count': 18,
                'join_date': 'February 15, 2025'
            }
        ]
    else:
        # When connected to DB:
        # from .models import Provider
        # return Provider.objects.all()
        pass

def get_system_stats(use_mock=USE_MOCK_DATA):
    """Get system statistics for admin dashboard."""
    if use_mock:
        return {
            'total_patients': 55,
            'total_providers': 3,
            'total_appointments': {
                'today': 8,
                'this_week': 42,
                'this_month': 167
            },
            'new_registrations': {
                'today': 2,
                'this_week': 12,
                'this_month': 35
            },
            'prescription_requests': {
                'pending': 15,
                'completed_today': 22
            },
            'system_uptime': '99.9%',
            'database_size': '1.2 GB'
        }
    else:
        # When connected to DB, calculate actual stats
        pass

def get_admin_logs(limit=100, use_mock=USE_MOCK_DATA):
    """Get system logs for admin dashboard."""
    if use_mock:
        return [
            {
                'timestamp': 'April 2, 2025 - 14:35:22',
                'user': 'dr.smith',
                'action': 'LOGIN',
                'ip_address': '192.168.1.100',
                'details': 'Successful login'
            },
            {
                'timestamp': 'April 2, 2025 - 14:32:15',
                'user': 'admin',
                'action': 'CREATE_USER',
                'ip_address': '192.168.1.5',
                'details': 'Created new provider account: dr.wilson'
            },
            {
                'timestamp': 'April 2, 2025 - 14:20:45',
                'user': 'system',
                'action': 'BACKUP',
                'ip_address': '127.0.0.1',
                'details': 'Daily backup completed successfully'
            },
            {
                'timestamp': 'April 2, 2025 - 13:45:12',
                'user': 'jane.doe',
                'action': 'PRESCRIPTION_REQUEST',
                'ip_address': '192.168.1.120',
                'details': 'Submitted prescription request for Lisinopril'
            }
        ]
    else:
        # When connected to DB, retrieve actual logs
        pass
