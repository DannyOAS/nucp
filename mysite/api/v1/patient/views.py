# mysite/api/v1/patient/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from patient.models import Patient, PrescriptionRequest
from common.models import Appointment, Prescription, Message
from .serializers import (
    PatientSerializer, PrescriptionRequestSerializer,
    AppointmentSerializer, PrescriptionSerializer, MessageSerializer
)
from .permissions import IsPatientOrReadOnly, IsPatientOwner
from .filters import (
    AppointmentFilter, PrescriptionFilter, 
    MessageFilter, PrescriptionRequestFilter
)
from api.versioning import VersionedViewMixin
from django.db.models import Q 

class PatientViewSet(VersionedViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows patients to view their own profile.
    Patients can only see their own profile.
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwner]
    version = 'v1'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'patient_profile'):
            return Patient.objects.filter(id=self.request.user.patient_profile.id)
        return Patient.objects.none()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current patient's profile"""
        if hasattr(request.user, 'patient_profile'):
            serializer = self.get_serializer(request.user.patient_profile)
            return Response(serializer.data)
        return Response({"detail": "Patient profile not found."}, status=404)

class AppointmentViewSet(VersionedViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for patient appointments.
    Patients can only see their own appointments.
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AppointmentFilter
    search_fields = ['reason', 'notes', 'doctor__user__last_name']
    ordering_fields = ['time', 'status']
    ordering = ['time']
    version = 'v1'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'patient_profile'):
            return Appointment.objects.filter(patient=self.request.user)
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming appointments"""
        now = timezone.now()
        queryset = self.get_queryset().filter(
            time__gt=now  # Future appointments
        ).exclude(
            status='Cancelled'  # Exclude cancelled appointments
        ).order_by('time')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get past appointments"""
        now = timezone.now()
        queryset = self.get_queryset().filter(time__lte=now).order_by('-time')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PrescriptionViewSet(VersionedViewMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for patient prescriptions.
    Patients can only see their own prescriptions.
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PrescriptionFilter
    search_fields = ['medication_name', 'instructions', 'doctor__user__last_name']
    ordering_fields = ['created_at', 'status', 'expires']
    ordering = ['-created_at']
    version = 'v1'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'patient_profile'):
            return Prescription.objects.filter(patient=self.request.user)
        return Prescription.objects.none()
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active prescriptions"""
        queryset = self.get_queryset().filter(status='Active')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PrescriptionRequestViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API endpoint for prescription requests.
    Patients can only see, create and modify their own prescription requests.
    """
    serializer_class = PrescriptionRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PrescriptionRequestFilter
    search_fields = ['medication_name', 'preferred_pharmacy']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    version = 'v1'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'patient_profile'):
            return PrescriptionRequest.objects.filter(patient=self.request.user.patient_profile)
        return PrescriptionRequest.objects.none()
    
    def perform_create(self, serializer):
        if hasattr(self.request.user, 'patient_profile'):
            serializer.save(patient=self.request.user.patient_profile)

class MessageViewSet(VersionedViewMixin, viewsets.ModelViewSet):
    """
    API endpoint for patient messages.
    Patients can see and create messages they've sent or received.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MessageFilter
    search_fields = ['subject', 'content']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    version = 'v1'
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Message.objects.none()
            
        # Get messages where the user is either the sender or recipient
        return Message.objects.filter(
            Q(recipient=self.request.user) & 
            ~Q(status='deleted')
        ) | Message.objects.filter(
            Q(sender=self.request.user)
        )
    
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
        serializer.save(sender=self.request.user, sender_type='patient')
