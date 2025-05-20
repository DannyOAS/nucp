# mysite/api/v1/provider/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from provider.models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument
from common.models import Appointment, Prescription, Message
from patient.models import Patient
from .serializers import (
    ProviderSerializer, AppointmentSerializer, PrescriptionSerializer,
    ClinicalNoteSerializer, DocumentTemplateSerializer, GeneratedDocumentSerializer,
    RecordingSessionSerializer, MessageSerializer
)
#from patient.api.serializers import PatientSerializer
from api.v1.patient.serializers import PatientSerializer
from .permissions import IsProvider, IsProviderOrReadOnly
from api.versioning import VersionedViewMixin
from django.db.models import Q

class ProviderViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider profiles
    """
    serializer_class = ProviderSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    version = 'v1'
    
    def get_queryset(self):
        # A provider can only see their own profile
        if hasattr(self.request.user, 'provider_profile'):
            return Provider.objects.filter(id=self.request.user.provider_profile.id)
        return Provider.objects.none()

class ProviderPatientsViewSet(VersionedViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    API v1 endpoint that allows providers to view patients assigned to them.
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsProvider]
    version = 'v1'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'provider_profile'):
            # Return patients where this provider is the primary provider
            return Patient.objects.filter(primary_provider=self.request.user.provider_profile)
        return Patient.objects.none()

class AppointmentViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider appointments
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name', 'type', 'status']
    ordering_fields = ['time', 'status']
    ordering = ['time']
    version = 'v1'
    
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

class PrescriptionViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider prescriptions
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['medication_name', 'patient__first_name', 'patient__last_name', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    version = 'v1'
    
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

class MessageViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for provider messages
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject', 'content', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    version = 'v1'
    
    def get_queryset(self):
        # A provider can see messages they've sent or received
        if hasattr(self.request.user, 'provider_profile'):
            # Get messages where the user is either the sender or recipient
            return Message.objects.filter(
                Q(sender=self.request.user) |
                Q(recipient=self.request.user)
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

class ClinicalNoteViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for clinical notes
    """
    serializer_class = ClinicalNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['provider_edited_text', 'ai_generated_text', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    version = 'v1'
    
    def get_queryset(self):
        # A provider can only see their own clinical notes
        if hasattr(self.request.user, 'provider_profile'):
            return ClinicalNote.objects.filter(provider=self.request.user.provider_profile)
        return ClinicalNote.objects.none()

class DocumentTemplateViewSet(VersionedViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    API v1 endpoint for document templates (read-only for providers)
    """
    serializer_class = DocumentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'template_type']
    ordering_fields = ['created_at', 'name']
    ordering = ['name']
    version = 'v1'
    
    def get_queryset(self):
        # Providers can see all active templates
        return DocumentTemplate.objects.filter(is_active=True)

class GeneratedDocumentViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for generated documents
    """
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['template__name', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    version = 'v1'
    
    def get_queryset(self):
        # A provider can only see documents they've generated
        if hasattr(self.request.user, 'provider_profile'):
            return GeneratedDocument.objects.filter(provider=self.request.user.provider_profile)
        return GeneratedDocument.objects.none()

class RecordingSessionViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API v1 endpoint for recording sessions
    """
    serializer_class = RecordingSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProviderOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['transcription_status']
    ordering_fields = ['start_time', 'transcription_status']
    ordering = ['-start_time']
    version = 'v1'
    
    def get_queryset(self):
        # A provider can only see their own recording sessions
        if hasattr(self.request.user, 'provider_profile'):
            return RecordingSession.objects.filter(provider=self.request.user.provider_profile)
        return RecordingSession.objects.none()
