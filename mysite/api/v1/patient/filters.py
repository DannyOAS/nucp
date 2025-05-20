# patient/api/filters.py
import django_filters
from patient.models import Patient, PrescriptionRequest
from common.models import Appointment, Prescription, Message

class AppointmentFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='time', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='time', lookup_expr='lte')
    type = django_filters.CharFilter(field_name='type', lookup_expr='iexact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    
    class Meta:
        model = Appointment
        fields = ['start_date', 'end_date', 'type', 'status', 'doctor']

class PrescriptionFilter(django_filters.FilterSet):
    medication_name = django_filters.CharFilter(field_name='medication_name', lookup_expr='icontains')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    
    class Meta:
        model = Prescription
        fields = ['medication_name', 'status', 'doctor']

class MessageFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    subject = django_filters.CharFilter(field_name='subject', lookup_expr='icontains')
    
    class Meta:
        model = Message
        fields = ['status', 'subject']

class PrescriptionRequestFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    medication_name = django_filters.CharFilter(field_name='medication_name', lookup_expr='icontains')
    
    class Meta:
        model = PrescriptionRequest
        fields = ['status', 'medication_name']
