from django.db import models
from django.contrib.auth.models import User

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    
    class Meta:
        ordering = ['-created_at']

class PatientRegistration(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    primary_phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    date_of_birth = models.DateField()
    address = models.TextField()
    ohip_number = models.CharField(max_length=12)
    current_medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    supplements = models.TextField(blank=True)
    pharmacy_details = models.CharField(max_length=200, blank=True)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_alternate_phone = models.CharField(max_length=20, blank=True)
    virtual_care_consent = models.BooleanField()
    ehr_consent = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    erpnext_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['-created_at']

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

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("blog_detail", kwargs={"pk": self.pk})
    
    class Meta:
        ordering = ['-created_at']

# Dashboard Models
class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.CharField(max_length=100)
    time = models.DateTimeField()
    type = models.CharField(max_length=50)  # e.g., "Virtual", "Clinic Visit"

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.time}"
    
    class Meta:
        ordering = ['time']

class Prescription(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    name = models.CharField(max_length=100)
    dose = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.dose}"
    
    class Meta:
        ordering = ['name']

#######################################################################################################################################
#MESSAGE MODELS
#######################################################################################################################################
class Message(models.Model):
    """Model for messages between patients and providers"""
    
    RECIPIENT_TYPES = [
        ('provider', 'Healthcare Provider'),
        ('patient', 'Patient'),
        ('pharmacy', 'Pharmacy'),
        ('billing', 'Billing Department'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES, default='provider')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}: {self.subject}"
    
    def mark_as_read(self):
        """Mark message as read with current timestamp"""
        from django.utils import timezone
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_unread(self):
        """Mark message as unread"""
        if self.status == 'read':
            self.status = 'unread'
            self.read_at = None
            self.save()
    
    def archive(self):
        """Archive the message"""
        if self.status != 'deleted':
            self.status = 'archived'
            self.save()
    
    def delete_message(self):
        """Soft delete the message"""
        self.status = 'deleted'
        self.save()

# New models for AI and Forms +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# AI Scribe Models
class RecordingSession(models.Model):
    """Model to store recording sessions for AI transcription"""
    TRANSCRIPTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    appointment = models.ForeignKey('Appointment', on_delete=models.CASCADE, related_name='recordings')
    jitsi_recording_id = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    storage_path = models.CharField(max_length=255, null=True, blank=True)
    transcription_status = models.CharField(
        max_length=50, 
        choices=TRANSCRIPTION_STATUS_CHOICES,
        default="pending"
    )
    transcription_text = models.TextField(blank=True)
    
    def __str__(self):
        return f"Recording {self.id} for Appointment {self.appointment.id}"


class ClinicalNote(models.Model):
    """Model for AI-generated and provider-edited clinical notes"""
    NOTE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'AI Generated'),
        ('reviewed', 'Provider Reviewed'),
        ('finalized', 'Finalized'),
    ]
    
    appointment = models.ForeignKey('Appointment', on_delete=models.CASCADE, related_name='clinical_notes')
    transcription = models.ForeignKey(RecordingSession, on_delete=models.SET_NULL, null=True, blank=True)
    ai_generated_text = models.TextField(blank=True)
    provider_edited_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=50, 
        choices=NOTE_STATUS_CHOICES,
        default="draft"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_notes")
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="edited_notes")
    
    def __str__(self):
        return f"Clinical Note for Appointment {self.appointment.id}"


# Form Template Models
class DocumentTemplate(models.Model):
    """Model for document templates (lab requisitions, sick notes, etc.)"""
    TEMPLATE_TYPE_CHOICES = [
        ('lab_req', 'Lab Requisition'),
        ('sick_note', 'Sick Note'),
        ('referral', 'Referral Letter'),
        ('insurance', 'Insurance Form'),
        ('prescription', 'Prescription Form'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    template_type = models.CharField(
        max_length=50, 
        choices=TEMPLATE_TYPE_CHOICES,
        default="other"
    )
    template_content = models.TextField()  # JSON or HTML structure
    requires_patient_data = models.BooleanField(default=True)
    requires_provider_data = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_templates")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_template_type_display()}: {self.name}"


class GeneratedDocument(models.Model):
    """Model for documents generated from templates"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('archived', 'Archived'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient_documents")
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE)
    document_data = models.TextField()  # JSON containing filled form data
    rendered_content = models.TextField(blank=True)  # The final HTML/text content
    pdf_storage_path = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES,
        default="draft"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_documents")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_documents")
    
    def __str__(self):
        return f"{self.template.name} for {self.patient.get_full_name()}"


# AI System Configuration
class AIModelConfig(models.Model):
    """Model for AI configuration settings"""
    MODEL_TYPE_CHOICES = [
        ('transcription', 'Medical Transcription'),
        ('clinical_notes', 'Clinical Notes Generation'),
        ('form_automation', 'Form Automation'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(
        max_length=50, 
        choices=MODEL_TYPE_CHOICES,
        default="other"
    )
    version = models.CharField(max_length=20)
    api_endpoint = models.CharField(max_length=255)
    configuration_data = models.TextField()  # JSON containing model parameters
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class AIUsageLog(models.Model):
    """Model to track AI usage and performance"""
    LOG_TYPE_CHOICES = [
        ('transcription', 'Transcription'),
        ('clinical_notes', 'Clinical Notes'),
        ('form_fill', 'Form Auto-fill'),
        ('other', 'Other'),
    ]
    
    RESULT_STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failure', 'Failure'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    model_config = models.ForeignKey(AIModelConfig, on_delete=models.SET_NULL, null=True)
    log_type = models.CharField(
        max_length=50, 
        choices=LOG_TYPE_CHOICES,
        default="other"
    )
    input_data_reference = models.CharField(max_length=255, blank=True)  # Reference to input data (file path, ID, etc.)
    processing_time_ms = models.IntegerField(default=0)  # Processing time in milliseconds
    result_status = models.CharField(
        max_length=50, 
        choices=RESULT_STATUS_CHOICES,
        default="success"
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.log_type} log for {self.user.username if self.user else 'Unknown user'}"
