# patient/models.py
from django.db import models
from django.contrib.auth.models import User
from provider.models import Provider

class Patient(models.Model):
    """Model for patient profiles"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    date_of_birth = models.DateField()
    ohip_number = models.CharField(max_length=10, unique=True)
    primary_phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    primary_provider = models.ForeignKey(
        Provider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_patients'
    )
    
    # Medical information
    current_medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    pharmacy_details = models.TextField(blank=True)
    
    # Consent fields
    virtual_care_consent = models.BooleanField(default=False)
    ehr_consent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional ERPNext integration
    erpnext_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
    
    @property
    def full_name(self):
        """Get patient's full name"""
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def age(self):
        """Calculate patient's age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_appointments(self):
        """Get all appointments for this patient"""
        return self.appointments.all().order_by('-time')
    
    def get_upcoming_appointments(self):
        """Get upcoming appointments"""
        from django.utils import timezone
        return self.appointments.filter(
            time__gte=timezone.now()
        ).order_by('time')
    
    def get_prescriptions(self):
        """Get all prescriptions for this patient"""
        return self.prescriptions.all().order_by('-created_at')
    
    def get_active_prescriptions(self):
        """Get active prescriptions"""
        return self.prescriptions.filter(
            status='Active'
        ).order_by('-created_at')
    
    def __str__(self):
        return f"{self.full_name} (OHIP: {self.ohip_number})"

class PrescriptionRequest(models.Model):
    """Model for prescription requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='prescription_requests',
        null=True,  # Add this line
        blank=True  # Add this line
    )
    medication_name = models.CharField(max_length=200)
    current_dosage = models.CharField(max_length=100)
    medication_duration = models.CharField(max_length=100)
    last_refill_date = models.DateField(null=True, blank=True)
    preferred_pharmacy = models.CharField(max_length=200)
    new_medical_conditions = models.TextField(blank=True)
    new_medications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    information_consent = models.BooleanField(default=False)
    pharmacy_consent = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Prescription request for {self.medication_name} by {self.patient.full_name}"
