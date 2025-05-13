# provider/api/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from provider.models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument
from common.models import Appointment, Prescription, Message
from .serializers import (
    ProviderSerializer, AppointmentSerializer, PrescriptionSerializer,
    ClinicalNoteSerializer, DocumentTemplateSerializer, GeneratedDocumentSerializer
)

class IsProviderOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow providers to edit their own data.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(request.user, 'provider_profile'):
            # Check if the object has a provider field
            if hasattr(obj, 'provider'):
                return obj.provider == request.user.provider_profile
            # Check if the object has a doctor field
            elif hasattr(obj, 'doctor'):
                return obj.doctor == request.user.provider_profile
        
        return False

class ProviderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for provider profiles
    """
    serializer_class = ProviderSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    
    def get_queryset(self):
        # A provider can only see their own profile
        if hasattr(self.request.user, 'provider_profile'):
            return Provider.objects.filter(id=self.request.user.provider_profile.id)
        return Provider.objects.none()

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for provider appointments
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name', 'type', 'status']
    ordering_fields = ['time', 'status']
    ordering = ['time']
    
    def get_queryset(self):
        # A provider can only see their own appointments
        if hasattr(self.request.user, 'provider_profile'):
            queryset = Appointment.objects.filter(doctor=self.request.user.provider_profile)
            
            # Filter by date if provided
            start_date = self.request.query_params.get('start_date', None)
            end_date = self.request.query_params.get('end_date', None)
            
            if start_date:
                queryset = queryset.filter(time__gte=start_date)
            if end_date:
                queryset = queryset.filter(time__lte=end_date)
                
            # Filter by status if provided
            status = self.request.query_params.get('status', None)
            if status:
                queryset = queryset.filter(status=status)
                
            return queryset
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's appointments"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            time__date=today
        ).order_by('time')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        now = timezone.now()
        queryset = self.get_queryset().filter(
            time__gt=now
        ).order_by('time')[:10]  # Limit to 10
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for provider prescriptions
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'patient__first_name', 'patient__last_name', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # A provider can only see prescriptions they've written
        if hasattr(self.request.user, 'provider_profile'):
            queryset = Prescription.objects.filter(doctor=self.request.user.provider_profile)
            
            # Filter by status if provided
            status = self.request.query_params.get('status', None)
            if status:
                queryset = queryset.filter(status=status)
                
            return queryset
        return Prescription.objects.none()
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending prescriptions"""
        queryset = self.get_queryset().filter(status='Pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active prescriptions"""
        queryset = self.get_queryset().filter(status='Active')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ClinicalNoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for clinical notes
    """
    serializer_class = ClinicalNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['provider_edited_text', 'ai_generated_text', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # A provider can only see their own clinical notes
        if hasattr(self.request.user, 'provider_profile'):
            return ClinicalNote.objects.filter(provider=self.request.user.provider_profile)
        return ClinicalNote.objects.none()

class DocumentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for document templates (read-only for providers)
    """
    serializer_class = DocumentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'template_type']
    ordering_fields = ['created_at', 'name']
    ordering = ['name']
    
    def get_queryset(self):
        # Providers can see all active templates
        return DocumentTemplate.objects.filter(is_active=True)

class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for generated documents
    """
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['template__name', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # A provider can only see documents they've generated
        if hasattr(self.request.user, 'provider_profile'):
            return GeneratedDocument.objects.filter(provider=self.request.user.provider_profile)
        return GeneratedDocument.objects.none()

# provider/api/serializers.py
# Add these serializers to the existing file

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
