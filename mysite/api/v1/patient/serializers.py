# patient/api/serializers.py
from rest_framework import serializers
from patient.models import Patient, PrescriptionRequest
from django.contrib.auth.models import User
from common.models import Appointment, Prescription, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'date_of_birth', 'ohip_number', 'primary_phone', 
                 'alternate_phone', 'address', 'emergency_contact_name', 'emergency_contact_phone',
                 'current_medications', 'allergies', 'pharmacy_details', 'primary_provider',
                 'virtual_care_consent', 'ehr_consent', 'full_name']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.full_name

class PrescriptionRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescriptionRequest
        fields = ['id', 'patient', 'medication_name', 'current_dosage', 'medication_duration',
                 'last_refill_date', 'preferred_pharmacy', 'new_medical_conditions',
                 'new_medications', 'side_effects', 'information_consent',
                 'pharmacy_consent', 'status', 'created_at', 'updated_at', 'patient_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        if obj.patient:
            return obj.patient.full_name
        return ""

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'time', 'type', 'status', 'reason',
                 'notes', 'patient_name', 'doctor_name']
        read_only_fields = ['id']
    
    def get_patient_name(self, obj):
        if hasattr(obj.patient, 'get_full_name'):
            return obj.patient.get_full_name()
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""
    
    def get_doctor_name(self, obj):
        if obj.doctor and hasattr(obj.doctor, 'user'):
            return f"Dr. {obj.doctor.user.last_name}"
        return ""

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = ['id', 'medication_name', 'dosage', 'instructions', 'patient', 'doctor',
                 'status', 'refills_remaining', 'expires', 'created_at', 'updated_at', 'patient_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        if hasattr(obj.patient, 'get_full_name'):
            return obj.patient.get_full_name()
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'subject', 'content', 'status',
                 'created_at', 'sender_name', 'recipient_name']
        read_only_fields = ['id', 'created_at']
    
    def get_sender_name(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        return ""
    
    def get_recipient_name(self, obj):
        if obj.recipient:
            return f"{obj.recipient.first_name} {obj.recipient.last_name}"
        return ""
