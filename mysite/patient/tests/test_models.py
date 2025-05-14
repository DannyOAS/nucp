# patient/tests/test_models.py
from django.test import TestCase
from patient.models import Patient, PrescriptionRequest
from django.contrib.auth.models import User

class PatientModelTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpassword'
        )
        
        # Create a patient
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth='1990-01-01',
            ohip_number='1234567890',
            primary_phone='123-456-7890',
            address='123 Test St',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='987-654-3210'
        )
    
    def test_patient_creation(self):
        """Test patient creation and properties"""
        self.assertEqual(self.patient.full_name, 'testpatient')
        self.assertEqual(self.patient.ohip_number, '1234567890')

class PrescriptionRequestModelTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@example.com',
            password='testpassword'
        )
        
        # Create a patient
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth='1990-01-01',
            ohip_number='1234567890',
            primary_phone='123-456-7890',
            address='123 Test St',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='987-654-3210'
        )
        
        # Create a prescription request
        self.prescription_request = PrescriptionRequest.objects.create(
            patient=self.patient,
            medication_name='Test Medication',
            current_dosage='10mg',
            medication_duration='2 months',
            preferred_pharmacy='Test Pharmacy',
            information_consent=True,
            pharmacy_consent=True
        )
    
    def test_prescription_request_creation(self):
        """Test prescription request creation"""
        self.assertEqual(self.prescription_request.medication_name, 'Test Medication')
        self.assertEqual(self.prescription_request.status, 'pending')
