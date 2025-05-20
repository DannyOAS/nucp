# provider/api/serializers.py
from rest_framework import serializers
from provider.models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument
from common.models import Appointment, Prescription, Message
from django.contrib.auth.models import User
from api.serializers import (
    UserSerializer as BaseUserSerializer,
    BaseProviderSerializer, 
    BaseAppointmentSerializer, 
    BasePrescriptionSerializer, 
    BaseMessageSerializer
)

# Extend the base UserSerializer if needed, otherwise use it directly
class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        # We can customize if needed
        pass

# Extend BaseProviderSerializer
class ProviderSerializer(BaseProviderSerializer):
    """V1 Provider serializer extending the base provider serializer"""
    
    # Override to use CharField as in the original
    full_name = serializers.CharField(read_only=True)
    
    class Meta(BaseProviderSerializer.Meta):
        model = Provider
        # Use the same fields as the base
        fields = BaseProviderSerializer.Meta.fields
        read_only_fields = ['id']

# Extend BaseAppointmentSerializer
class AppointmentSerializer(BaseAppointmentSerializer):
    """V1 Appointment serializer extending the base appointment serializer"""
    
    class Meta(BaseAppointmentSerializer.Meta):
        model = Appointment
        fields = BaseAppointmentSerializer.Meta.fields
        read_only_fields = ['id']
    
    # We're keeping the same implementation as the base class
    # No need to override get_patient_name or get_doctor_name unless the logic changes

# Extend BasePrescriptionSerializer
class PrescriptionSerializer(BasePrescriptionSerializer):
    """V1 Prescription serializer extending the base prescription serializer"""
    
    class Meta(BasePrescriptionSerializer.Meta):
        model = Prescription
        # Customize fields if needed - here we're removing doctor_name which was in the base
        fields = ['id', 'medication_name', 'dosage', 'patient', 'doctor', 'status', 'refills', 
                 'refills_remaining', 'created_at', 'updated_at', 'patient_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    # Keep original implementation if it differs from base
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else ""

# Extend BaseMessageSerializer
class MessageSerializer(BaseMessageSerializer):
    """V1 Message serializer extending the base message serializer"""
    
    class Meta(BaseMessageSerializer.Meta):
        model = Message
        fields = BaseMessageSerializer.Meta.fields
        # Customize read_only_fields to include sender
        read_only_fields = ['id', 'sender', 'created_at', 'sender_name', 'recipient_name']
    
    # Keep the same implementations for the get methods unless they differ from base

# The following serializers don't have base classes, so they remain unchanged
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
