# api/filters.py
import django_filters
from patient.models import Patient, PrescriptionRequest
from provider.models import Provider
from common.models import Appointment, Prescription, Message
from django.db import models

class BaseAppointmentFilter(django_filters.FilterSet):
    """Base filter for appointments"""
    start_date = django_filters.DateTimeFilter(field_name='time', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='time', lookup_expr='lte')
    type = django_filters.CharFilter(field_name='type', lookup_expr='iexact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    
    class Meta:
        model = Appointment
        fields = ['start_date', 'end_date', 'type', 'status', 'patient', 'doctor']

class BasePrescriptionFilter(django_filters.FilterSet):
    """Base filter for prescriptions"""
    medication_name = django_filters.CharFilter(field_name='medication_name', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Prescription
        fields = ['medication_name', 'status', 'patient', 'doctor']

class BasePrescriptionRequestFilter(django_filters.FilterSet):
    """Base filter for prescription requests"""
    medication_name = django_filters.CharFilter(field_name='medication_name', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = PrescriptionRequest
        fields = ['medication_name', 'status', 'patient']

class BaseMessageFilter(django_filters.FilterSet):
    """Base filter for messages"""
    subject = django_filters.CharFilter(field_name='subject', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Message
        fields = ['subject', 'status', 'sender', 'recipient']

class BasePatientFilter(django_filters.FilterSet):
    """Base filter for patients"""
    name = django_filters.CharFilter(method='filter_name')
    ohip_number = django_filters.CharFilter(lookup_expr='iexact')
    
    class Meta:
        model = Patient
        fields = ['name', 'ohip_number', 'primary_provider']
    
    def filter_name(self, queryset, name, value):
        """Filter by patient name (first or last name)"""
        return queryset.filter(
            models.Q(user__first_name__icontains=value) | 
            models.Q(user__last_name__icontains=value)
        )

class BaseProviderFilter(django_filters.FilterSet):
    """Base filter for providers"""
    name = django_filters.CharFilter(method='filter_name')
    specialty = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = Provider
        fields = ['name', 'specialty', 'is_active']
    
    def filter_name(self, queryset, name, value):
        """Filter by provider name (first or last name)"""
        return queryset.filter(
            models.Q(user__first_name__icontains=value) | 
            models.Q(user__last_name__icontains=value)
        )
