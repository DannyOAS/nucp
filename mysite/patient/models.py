
# patient/models.py - ENHANCED VERSION
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from provider.models import Provider
from .validators import (
    validate_ohip_number, 
    validate_canadian_phone, 
    validate_medication_name,
    validate_dosage,
    validate_postal_code
)

class Patient(models.Model):
    """SECURED: Patient model with comprehensive validation"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    date_of_birth = models.DateField()
    
    # CRITICAL: OHIP number with validation
    ohip_number = models.CharField(
        max_length=12, 
        unique=True,
        validators=[validate_ohip_number],
        help_text="Format: 1234567890AB"
    )
    
    # CRITICAL: Phone numbers with validation
    primary_phone = models.CharField(
        max_length=20,
        validators=[validate_canadian_phone]
    )
    alternate_phone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[validate_canadian_phone]
    )
    
    # Address validation
    address = models.TextField(
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\.,#]+$',
                message='Address contains invalid characters.'
            )
        ]
    )
    
    # Emergency contact validation
    emergency_contact_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\.]+$',
                message='Name contains invalid characters.'
            )
        ]
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        validators=[validate_canadian_phone]
    )
    
    primary_provider = models.ForeignKey(
        Provider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_patients'
    )
    
    # Medical information with validation
    current_medications = models.TextField(
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\(\)\./,%\n\r]+$',
                message='Medications field contains invalid characters.'
            )
        ]
    )
    allergies = models.TextField(
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\(\)\./,%\n\r]+$',
                message='Allergies field contains invalid characters.'
            )
        ]
    )
    
    # Other fields...
    pharmacy_details = models.TextField(blank=True)
    virtual_care_consent = models.BooleanField(default=False)
    ehr_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    erpnext_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['ohip_number']),
            models.Index(fields=['user']),
            models.Index(fields=['primary_provider']),
        ]
    
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
    
    def clean(self):
        """Additional model-level validation"""
        super().clean()
        
        # Validate date of birth is not in the future
        from django.utils import timezone
        from datetime import date
        
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError({'date_of_birth': 'Date of birth cannot be in the future.'})
        
        # Validate age is reasonable (not over 150 years old)
        if self.date_of_birth:
            age = date.today().year - self.date_of_birth.year
            if age > 150:
                raise ValidationError({'date_of_birth': 'Invalid date of birth.'})
    
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
    """SECURED: Prescription request with validation"""
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
        null=True,
        blank=True
    )
    
    # CRITICAL: Medication name with validation
    medication_name = models.CharField(
        max_length=200,
        validators=[validate_medication_name]
    )
    
    # CRITICAL: Dosage with validation
    current_dosage = models.CharField(
        max_length=100,
        validators=[validate_dosage]
    )
    
    medication_duration = models.CharField(max_length=100)
    last_refill_date = models.DateField(null=True, blank=True)
    preferred_pharmacy = models.CharField(max_length=200)
    
    # Medical fields with validation
    new_medical_conditions = models.TextField(
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\(\)\./,%\n\r]+$',
                message='Medical conditions field contains invalid characters.'
            )
        ]
    )
    new_medications = models.TextField(
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\(\)\./,%\n\r]+$',
                message='Medications field contains invalid characters.'
            )
        ]
    )
    side_effects = models.TextField(
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\(\)\./,%\n\r]+$',
                message='Side effects field contains invalid characters.'
            )
        ]
    )
    
    information_consent = models.BooleanField(default=False)
    pharmacy_consent = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """Additional model-level validation"""
        super().clean()
        
        # Validate consents are given
        if not self.information_consent:
            raise ValidationError({'information_consent': 'Information consent is required.'})
        
        if not self.pharmacy_consent:
            raise ValidationError({'pharmacy_consent': 'Pharmacy consent is required.'})
        
        # Validate last refill date is not in the future
        from datetime import date
        if self.last_refill_date and self.last_refill_date > date.today():
            raise ValidationError({'last_refill_date': 'Last refill date cannot be in the future.'})
    
    def __str__(self):
        return f"Prescription request for {self.medication_name} by {self.patient.full_name if self.patient else 'Unknown'}"
