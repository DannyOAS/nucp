from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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

class Message(models.Model):
    """Model for messages between patients and providers"""
    
    RECIPIENT_TYPES = [
        ('provider', 'Healthcare Provider'),
        ('patient', 'Patient'),
        ('pharmacy', 'Pharmacy'),
        ('billing', 'Billing Department'),
        ('staff', 'Staff Member'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
        ('draft', 'Draft'),
    ]
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High Priority'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES, default='provider')
    sender_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES, null=True, blank=True)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    thread_id = models.CharField(max_length=50, null=True, blank=True)
    added_to_record = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}: {self.subject}"
    
    def mark_as_read(self):
        """Mark message as read with current timestamp"""
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
    
    def restore(self):
        """Restore message from archived or deleted status"""
        if self.status in ['archived', 'deleted']:
            self.status = 'read'
            self.save()

class MessageAttachment(models.Model):
    """Model for message attachments"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # Size in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment {self.file_name} for Message {self.message.id}"
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.1f} {unit}"
            size /= 1024
