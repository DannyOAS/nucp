# provider/api/serializers.py
from rest_framework import serializers
from provider.models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument
from common.models import Appointment, Prescription, Message
from django.contrib.auth.models import User
from common.models import Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']

class ProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Provider
        fields = ['id', 'user', 'license_number', 'specialty', 'bio', 'phone', 'is_active', 'full_name']
        read_only_fields = ['id']

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'time', 'type', 'status', 'reason', 'notes', 'patient_name', 'doctor_name']
        read_only_fields = ['id']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""
    
    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.last_name}" if obj.doctor and obj.doctor.user else ""

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = ['id', 'name', 'dose', 'patient', 'doctor', 'status', 'refills', 
                 'refills_remaining', 'created_at', 'updated_at', 'patient_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'subject', 'content', 
                 'status', 'created_at', 'sender_name', 'recipient_name']
        read_only_fields = ['id', 'sender', 'created_at', 'sender_name', 'recipient_name']
    
    def get_sender_name(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        return ""
    
    def get_recipient_name(self, obj):
        if obj.recipient:
            return f"{obj.recipient.first_name} {obj.recipient.last_name}"
        return ""

class RecordingSessionSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = RecordingSession
        fields = ['id', 'appointment', 'provider', 'jitsi_recording_id', 'start_time', 
                 'end_time', 'storage_path', 'transcription_status', 'transcription_text',
                 'patient_name', 'duration']
    
    def get_patient_name(self, obj):
        if obj.appointment and obj.appointment.patient:
            return f"{obj.appointment.patient.first_name} {obj.appointment.patient.last_name}"
        return "Unknown"
    
    def get_duration(self, obj):
        if obj.end_time and obj.start_time:
            return (obj.end_time - obj.start_time).total_seconds() // 60
        return None

class ClinicalNoteSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ClinicalNote
        fields = ['id', 'appointment', 'provider', 'transcription', 'ai_generated_text',
                 'provider_edited_text', 'status', 'created_at', 'updated_at',
                 'created_by', 'last_edited_by', 'patient_name']
    
    def get_patient_name(self, obj):
        if obj.appointment and obj.appointment.patient:
            return f"{obj.appointment.patient.first_name} {obj.appointment.patient.last_name}"
        return "Unknown"

class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = ['id', 'name', 'description', 'template_type', 'template_content',
                 'requires_patient_data', 'requires_provider_data', 'created_at',
                 'updated_at', 'created_by', 'is_active']

class GeneratedDocumentSerializer(serializers.ModelSerializer):
    template_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    html_content = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedDocument
        fields = ['id', 'patient', 'provider', 'template', 'document_data', 
                 'rendered_content', 'pdf_storage_path', 'status', 'created_at',
                 'updated_at', 'created_by', 'approved_by', 'template_name',
                 'patient_name', 'html_content']
    
    def get_template_name(self, obj):
        return obj.template.name if obj.template else "Unknown"
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return "Unknown"
    
    def get_html_content(self, obj):
        # In a real implementation, this would render the HTML content
        # For now, just return a placeholder
        return obj.rendered_content or "<p>Preview not available</p>"
