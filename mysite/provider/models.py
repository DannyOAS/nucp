from django.db import models
from django.contrib.auth.models import User
from common.models import Appointment, Prescription, Message

class Provider(models.Model):
    """Model for healthcare providers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    license_number = models.CharField(max_length=50, unique=True)
    specialty = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Dr. {self.user.last_name}"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def get_appointments(self, start_date=None, end_date=None, view_type='week'):
        """Get provider appointments, optionally filtered by date range"""
        appointments = Appointment.objects.filter(doctor=self)
        if start_date:
            appointments = appointments.filter(time__gte=start_date)
        if end_date:
            appointments = appointments.filter(time__lte=end_date)
        return appointments.order_by('time')
    
    def get_patients(self):
        """Get all patients associated with this provider"""
        from theme_name.models import PatientRegistration
        
        # Check if provider field exists in PatientRegistration
        if hasattr(PatientRegistration, 'provider'):
            # Use the provider field if it exists
            return PatientRegistration.objects.filter(provider=self)
        else:
            # Alternative approach: Get patients from appointments
            from common.models import Appointment
            patient_ids = Appointment.objects.filter(doctor=self).values_list('patient_id', flat=True).distinct()
            return PatientRegistration.objects.filter(id__in=patient_ids)
    
    def get_prescription_requests(self):
        """Get pending prescription requests for this provider"""
        return Prescription.objects.filter(doctor=self, status='Pending')

class RecordingSession(models.Model):
    """Model to store recording sessions for AI transcription"""
    TRANSCRIPTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='recordings')
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='recordings')
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
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='clinical_notes')
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
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="generated_documents")
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
