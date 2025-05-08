from django.db import models
from django.contrib.auth.models import User
from common.models import Appointment, Prescription, Message  # Import shared models

class RecordingSession(models.Model):
    """Model to store recording sessions for AI transcription"""
    TRANSCRIPTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='recordings')
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
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='clinical_notes')
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
