# patient/api/serializers.py
from rest_framework import serializers
from patient.models import Patient, PrescriptionRequest
from django.contrib.auth.models import User
from common.models import Appointment, Prescription, Message
from api.serializers import (
    BasePatientSerializer, 
    UserSerializer as BaseUserSerializer,
    BaseAppointmentSerializer,
    BasePrescriptionSerializer,
    BasePrescriptionRequestSerializer,
    BaseMessageSerializer
)

# Extend the base UserSerializer 
class UserSerializer(BaseUserSerializer):
    """V1 User serializer extending the base user serializer"""
    class Meta(BaseUserSerializer.Meta):
        # We can keep the same fields or customize if needed
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']

# Extend BasePatientSerializer - we can see it's already imported but not used
class PatientSerializer(BasePatientSerializer):
    """V1 Patient serializer extending the base patient serializer"""
    
    class Meta(BasePatientSerializer.Meta):
        model = Patient
        # Extend the fields from the base serializer
        fields = BasePatientSerializer.Meta.fields + [
            'current_medications', 'allergies', 'pharmacy_details',
            'virtual_care_consent', 'ehr_consent'
        ]
        read_only_fields = ['id']
    
    # Override the get_full_name method to use obj.full_name directly
    def get_full_name(self, obj):
        return obj.full_name

# Extend BasePrescriptionRequestSerializer
class PrescriptionRequestSerializer(BasePrescriptionRequestSerializer):
    """V1 Prescription Request serializer extending the base serializer"""
    
    class Meta(BasePrescriptionRequestSerializer.Meta):
        model = PrescriptionRequest
        fields = BasePrescriptionRequestSerializer.Meta.fields
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    # Simplified implementation compared to base
    def get_patient_name(self, obj):
        if obj.patient:
            return obj.patient.full_name
        return ""

# Extend BaseAppointmentSerializer
class AppointmentSerializer(BaseAppointmentSerializer):
    """V1 Appointment serializer extending the base appointment serializer"""
    
    class Meta(BaseAppointmentSerializer.Meta):
        model = Appointment
        fields = BaseAppointmentSerializer.Meta.fields
        read_only_fields = ['id']
    
    # Custom implementation using get_full_name if available
    def get_patient_name(self, obj):
        if hasattr(obj.patient, 'get_full_name'):
            return obj.patient.get_full_name()
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""

# Extend BasePrescriptionSerializer
class PrescriptionSerializer(BasePrescriptionSerializer):
    """V1 Prescription serializer extending the base prescription serializer"""
    
    class Meta(BasePrescriptionSerializer.Meta):
        model = Prescription
        # Just slightly different field list from base
        fields = ['id', 'medication_name', 'dosage', 'instructions', 'patient', 'doctor',
                 'status', 'refills_remaining', 'expires', 'created_at', 'updated_at', 'patient_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    # Custom implementation using get_full_name if available
    def get_patient_name(self, obj):
        if hasattr(obj.patient, 'get_full_name'):
            return obj.patient.get_full_name()
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""

# Extend BaseMessageSerializer
class MessageSerializer(BaseMessageSerializer):
    """V1 Message serializer extending the base message serializer"""
    
    class Meta(BaseMessageSerializer.Meta):
        model = Message
        fields = BaseMessageSerializer.Meta.fields
        read_only_fields = ['id', 'created_at']
    
    # We're keeping the same implementation as the base
    # No need to override get_sender_name or get_recipient_name methods
    # unless the logic differs from the base class
