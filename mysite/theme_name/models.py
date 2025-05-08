from django.db import models
from django.contrib.auth.models import User
from django.db.models import SET_NULL

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
    """Patient registration model"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    primary_phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    date_of_birth = models.DateField()
    address = models.TextField()
    ohip_number = models.CharField(max_length=10)
    current_medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    pharmacy_details = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_alternate_phone = models.CharField(max_length=20, blank=True)
    virtual_care_consent = models.BooleanField(default=False)
    ehr_consent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    supplements = models.TextField(blank=True)
    erpnext_id = models.CharField(max_length=50, blank=True)
    
    # Add provider field
    provider = models.ForeignKey(
        'provider.Provider', 
        on_delete=SET_NULL, 
        null=True, 
        blank=True, 
        related_name='patients'
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class DemoRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    organization = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    user_type = models.CharField(max_length=20, choices=[
        ('provider', 'Healthcare Provider'),
        ('patient', 'Patient'),
        ('admin', 'Healthcare Administrator'),
        ('other', 'Other')
    ])
    message = models.TextField(blank=True)
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=20, choices=[
        ('morning', 'Morning (9am-12pm)'),
        ('afternoon', 'Afternoon (1pm-5pm)'),
        ('evening', 'Evening (5pm-7pm)')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Demo Request from {self.name} ({self.email})"

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
