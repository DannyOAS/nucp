from django.db import models
from django.contrib.auth.models import User

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
