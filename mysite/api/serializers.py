# api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from patient.models import Patient, PrescriptionRequest
from provider.models import Provider
from common.models import Appointment, Prescription, Message

class UserSerializer(serializers.ModelSerializer):
    """Base User serializer for both patients and providers"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active']
        read_only_fields = ['id', 'username', 'is_active']

class GroupSerializer(serializers.ModelSerializer):
    """Serializer for user groups"""
    class Meta:
        model = Group
        fields = ['id', 'name']
        read_only_fields = ['id', 'name']

class BasePatientSerializer(serializers.ModelSerializer):
    """Base serializer for patient data"""
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'date_of_birth', 'ohip_number', 'primary_phone', 
            'alternate_phone', 'address', 'emergency_contact_name', 
            'emergency_contact_phone', 'primary_provider', 'full_name'
        ]
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else ""

class BaseProviderSerializer(serializers.ModelSerializer):
    """Base serializer for provider data"""
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id', 'user', 'license_number', 'specialty', 'bio', 
            'phone', 'is_active', 'full_name'
        ]
        read_only_fields = ['id', 'is_active']
    
    def get_full_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}" if obj.user else ""

class BaseAppointmentSerializer(serializers.ModelSerializer):
    """Base serializer for appointment data"""
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'time', 'type', 'status', 
            'reason', 'notes', 'patient_name', 'doctor_name'
        ]
        read_only_fields = ['id']
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return ""
    
    def get_doctor_name(self, obj):
        if obj.doctor and hasattr(obj.doctor, 'user'):
            return f"Dr. {obj.doctor.user.last_name}"
        return ""

class BasePrescriptionSerializer(serializers.ModelSerializer):
    """Base serializer for prescription data"""
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'medication_name', 'dosage', 'instructions', 'patient', 
            'doctor', 'status', 'refills_remaining', 'expires', 
            'created_at', 'updated_at', 'patient_name', 'doctor_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return ""
    
    def get_doctor_name(self, obj):
        if obj.doctor and hasattr(obj.doctor, 'user'):
            return f"Dr. {obj.doctor.user.last_name}"
        return ""

class BasePrescriptionRequestSerializer(serializers.ModelSerializer):
    """Base serializer for prescription request data"""
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescriptionRequest
        fields = [
            'id', 'patient', 'medication_name', 'current_dosage', 
            'medication_duration', 'last_refill_date', 'preferred_pharmacy', 
            'new_medical_conditions', 'new_medications', 'side_effects', 
            'information_consent', 'pharmacy_consent', 'status', 
            'created_at', 'updated_at', 'patient_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        if obj.patient and hasattr(obj.patient, 'full_name'):
            return obj.patient.full_name
        return ""

class BaseMessageSerializer(serializers.ModelSerializer):
    """Base serializer for message data"""
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'recipient', 'subject', 'content', 
            'status', 'created_at', 'sender_name', 'recipient_name'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_sender_name(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        return ""
    
    def get_recipient_name(self, obj):
        if obj.recipient:
            return f"{obj.recipient.first_name} {obj.recipient.last_name}"
        return ""
