# provider/api/views.py (Updated)
from rest_framework import viewsets, permissions, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from provider.models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument
from common.models import Appointment, Prescription, Message
from .serializers import (
    ProviderSerializer, AppointmentSerializer, PrescriptionSerializer,
    ClinicalNoteSerializer, DocumentTemplateSerializer, GeneratedDocumentSerializer,
    RecordingSessionSerializer, MessageSerializer
)
from django.db import models  # For Q objects
from patient.models import Patient
#from patient.api.serializers import PatientSerializer  # Import the existing patient serializer
from api.v1.patient.serializers import PatientSerializer
from .permissions import IsProvider  # Import the permission from the new file
from .pagination import VersionedPagination  # Import the custom pagination class

class ProviderAPIVersionMixin:
    """Mixin to add API version information to all provider API viewsets"""
    version = 'v1'
    pagination_class = VersionedPagination
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['version'] = self.version
        return context
    
    def initialize_request(self, request, *args, **kwargs):
        """Add version to request object for use by the pagination class"""
        request = super().initialize_request(request, *args, **kwargs)
        request.version = self.version
        return request
        
    def get_paginated_response(self, data):
        """
        Override to ensure version information is included in custom action responses
        that use pagination.
        """
        response = super().get_paginated_response(data)
        if hasattr(response, 'data') and isinstance(response.data, dict):
            response.data['api_version'] = self.version
        return response
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add version information to non-paginated responses, such as detail views
        and custom actions that don't use pagination.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Only add version to successful responses with data
        if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
            if hasattr(response, 'data') and isinstance(response.data, dict):
                # Don't override if already set by pagination
                if 'api_version' not in response.data:
                    response.data['api_version'] = self.version
                    
        return response

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

class ProviderViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider profiles
    """
    serializer_class = ProviderSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    
    def get_queryset(self):
        # A provider can only see their own profile
        if hasattr(self.request.user, 'provider_profile'):
            return Provider.objects.filter(id=self.request.user.provider_profile.id)
        return Provider.objects.none()

class ProviderPatientsViewSet(ProviderAPIVersionMixin, viewsets.ReadOnlyModelViewSet):
    """
    API v1 endpoint that allows providers to view patients assigned to them.
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsProvider]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'provider_profile'):
            # Return patients where this provider is the primary provider
            return Patient.objects.filter(primary_provider=self.request.user.provider_profile)
        return Patient.objects.none()

class AppointmentViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider appointments
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

class PrescriptionViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider prescriptions
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['medication_name', 'patient__first_name', 'patient__last_name', 'status']
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

class MessageViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'content', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # A provider can see messages they've sent or received
        if hasattr(self.request.user, 'provider_profile'):
            # Get messages where the user is either the sender or recipient
            return Message.objects.filter(
                models.Q(sender=self.request.user) |
                models.Q(recipient=self.request.user)
            ).order_by('-created_at')
        return Message.objects.none()
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get received messages"""
        queryset = Message.objects.filter(
            recipient=request.user
        ).exclude(
            status='deleted'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get sent messages"""
        queryset = Message.objects.filter(
            sender=request.user
        ).order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, sender_type='provider')

class ClinicalNoteViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for clinical notes
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

class DocumentTemplateViewSet(ProviderAPIVersionMixin, viewsets.ReadOnlyModelViewSet):
    """
    API v1 endpoint for document templates (read-only for providers)
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

class GeneratedDocumentViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for generated documents
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

class RecordingSessionViewSet(ProviderAPIVersionMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for recording sessions
    """
    serializer_class = RecordingSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['transcription_status']
    ordering_fields = ['start_time', 'transcription_status']
    ordering = ['-start_time']
    
    def get_queryset(self):
        # A provider can only see their own recording sessions
        if hasattr(self.request.user, 'provider_profile'):
            return RecordingSession.objects.filter(provider=self.request.user.provider_profile)
        return RecordingSession.objects.none()
