# patient/forms.py - SECURED VERSION WITH VALIDATION
from django import forms
from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.exceptions import ValidationError
from common.models import Message
from patient.models import PrescriptionRequest, Patient
from patient.validators import (
    validate_ohip_number, 
    validate_canadian_phone, 
    validate_medication_name,
    validate_dosage
)
from datetime import date, timedelta
import re

class SecurePatientProfileEditForm(forms.Form):
    """SECURED: Patient profile form with comprehensive validation"""
    
    first_name = forms.CharField(
        max_length=100, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message='First name can only contain letters, spaces, hyphens, apostrophes, and periods.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message='Last name can only contain letters, spaces, hyphens, apostrophes, and periods.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': 'email@example.com'
        })
    )
    
    primary_phone = forms.CharField(
        max_length=20, 
        required=True,
        validators=[validate_canadian_phone],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': '(416) 555-1234'
        })
    )
    
    alternate_phone = forms.CharField(
        max_length=20, 
        required=False,
        validators=[validate_canadian_phone],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': '(416) 555-1234 (Optional)'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': '123 Main St\nToronto, ON M5V 1A1'
        }), 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s\-\.,#\n\r]+$',
                message='Address contains invalid characters.'
            )
        ]
    )
    
    emergency_contact_name = forms.CharField(
        max_length=100, 
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s\-\'\.]+$',
                message='Emergency contact name can only contain letters, spaces, hyphens, apostrophes, and periods.'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': 'Emergency Contact Name'
        })
    )
    
    emergency_contact_phone = forms.CharField(
        max_length=20, 
        required=True,
        validators=[validate_canadian_phone],
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]',
            'placeholder': '(416) 555-1234'
        })
    )
    
    def clean_email(self):
        """Additional email validation"""
        email = self.cleaned_data.get('email')
        if email:
            # Check for dangerous patterns
            dangerous_patterns = [
                r'<script',
                r'javascript:',
                r'<iframe',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, email, re.IGNORECASE):
                    raise ValidationError('Invalid email format.')
        
        return email
    
    def clean_address(self):
        """Additional address validation"""
        address = self.cleaned_data.get('address')
        if address:
            # Check length
            if len(address) > 500:
                raise ValidationError('Address is too long. Maximum 500 characters.')
            
            # Check for Canadian postal code pattern
            if not re.search(r'[A-Z]\d[A-Z]\s*\d[A-Z]\d', address.upper()):
                raise ValidationError('Please include a valid Canadian postal code in your address.')
        
        return address

class SecurePrescriptionRequestForm(forms.ModelForm):
    """SECURED: Prescription request form with comprehensive validation"""
    
    class Meta:
        model = PrescriptionRequest
        fields = [
            'medication_name', 
            'current_dosage', 
            'medication_duration', 
            'last_refill_date',
            'preferred_pharmacy', 
            'new_medical_conditions', 
            'new_medications', 
            'side_effects',
            'information_consent', 
            'pharmacy_consent'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom validation and styling to all fields
        self.fields['medication_name'].validators.append(validate_medication_name)
        self.fields['current_dosage'].validators.append(validate_dosage)
        
        # Add CSS classes and security attributes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({
                    'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
                    'autocomplete': 'off',  # Security: Prevent autocomplete
                    'spellcheck': 'false'   # Security: Prevent spellcheck data leakage
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
                    'autocomplete': 'off',
                    'spellcheck': 'false'
                })
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({
                    'class': 'shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline',
                    'type': 'date'
                })
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]'
                })
    
    def clean_medication_name(self):
        """Enhanced medication name validation"""
        medication_name = self.cleaned_data.get('medication_name')
        if medication_name:
            # Additional validation beyond the validator
            medication_name = medication_name.strip()
            
            # Check against common dangerous/invalid entries
            invalid_entries = [
                'test', 'testing', 'asdf', 'qwerty', '123', 'abc',
                'none', 'n/a', 'unknown', 'drug', 'medicine'
            ]
            
            if medication_name.lower() in invalid_entries:
                raise ValidationError('Please enter a valid medication name.')
            
            # Check for minimum length
            if len(medication_name) < 3:
                raise ValidationError('Medication name must be at least 3 characters long.')
        
        return medication_name
    
    def clean_last_refill_date(self):
        """Validate last refill date"""
        last_refill_date = self.cleaned_data.get('last_refill_date')
        if last_refill_date:
            # Cannot be in the future
            if last_refill_date > date.today():
                raise ValidationError('Last refill date cannot be in the future.')
            
            # Cannot be more than 5 years ago (reasonable limit)
            if last_refill_date < date.today() - timedelta(days=5*365):
                raise ValidationError('Last refill date cannot be more than 5 years ago.')
        
        return last_refill_date
    
    def clean(self):
        """Additional form-level validation"""
        cleaned_data = super().clean()
        
        # Ensure both consents are checked
        info_consent = cleaned_data.get('information_consent')
        pharmacy_consent = cleaned_data.get('pharmacy_consent')
        
        if not info_consent:
            raise ValidationError('Information consent is required to submit a prescription request.')
        
        if not pharmacy_consent:
            raise ValidationError('Pharmacy consent is required to submit a prescription request.')
        
        return cleaned_data

class SecurePatientMessageForm(forms.ModelForm):
    """SECURED: Patient message form with validation"""
    
    recipient_type = forms.ChoiceField(
        choices=[
            ('provider', 'My Healthcare Provider'),
            ('pharmacy', 'Pharmacy'),
            ('billing', 'Billing Department')
        ],
        widget=forms.Select(attrs={
            "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm"
        })
    )
    
    class Meta:
        model = Message
        fields = ['recipient_type', 'subject', 'content']
        widgets = {
            'subject': forms.TextInput(attrs={
                "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm",
                "placeholder": "Subject",
                "maxlength": "200",
                "autocomplete": "off",
                "spellcheck": "false"
            }),
            'content': forms.Textarea(attrs={
                "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm",
                "placeholder": "Your message here",
                "rows": 5,
                "maxlength": "5000",
                "autocomplete": "off",
                "spellcheck": "false"
            })
        }
    
    def clean_subject(self):
        """Validate message subject"""
        subject = self.cleaned_data.get('subject')
        if subject:
            subject = subject.strip()
            
            # Check for dangerous patterns
            dangerous_patterns = [
                r'<script',
                r'javascript:',
                r'<iframe',
                r'<object',
                r'<embed',
                r'eval\(',
                r'alert\(',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, subject, re.IGNORECASE):
                    raise ValidationError('Invalid subject format.')
            
            # Check length
            if len(subject) < 3:
                raise ValidationError('Subject must be at least 3 characters long.')
            
            if len(subject) > 200:
                raise ValidationError('Subject must be less than 200 characters.')
        
        return subject
    
    def clean_content(self):
        """Validate message content"""
        content = self.cleaned_data.get('content')
        if content:
            content = content.strip()
            
            # Check for dangerous patterns
            dangerous_patterns = [
                r'<script',
                r'javascript:',
                r'<iframe',
                r'<object',
                r'<embed',
                r'eval\(',
                r'alert\(',
                r'document\.',
                r'window\.',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    raise ValidationError('Invalid message content.')
            
            # Check length
            if len(content) < 10:
                raise ValidationError('Message content must be at least 10 characters long.')
            
            if len(content) > 5000:
                raise ValidationError('Message content must be less than 5000 characters.')
        
        return content
