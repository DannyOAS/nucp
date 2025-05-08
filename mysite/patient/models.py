from django.db import models
from common.models import Appointment, Prescription, Message  # Import shared models

class PrescriptionRequest(models.Model):
    # Patient Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    ohip_number = models.CharField(max_length=12)
    phone_number = models.CharField(max_length=20)

    # Prescription Details
    medication_name = models.CharField(max_length=200)
    current_dosage = models.CharField(max_length=100)
    medication_duration = models.CharField(max_length=100)
    last_refill_date = models.DateField()
    preferred_pharmacy = models.CharField(max_length=200)

    # Medical History
    new_medical_conditions = models.TextField(blank=True)
    new_medications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)

    # Consent
    information_consent = models.BooleanField()
    pharmacy_consent = models.BooleanField()

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription Request - {self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['-created_at']
