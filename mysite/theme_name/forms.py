from django import forms
from django.core.validators import FileExtensionValidator
from .models import ContactMessage, PatientRegistration, PrescriptionRequest, Appointment, Message, DemoRequest
from datetime import date, timedelta

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Your Name"}),
            "email": forms.EmailInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Your Email"}),
            "message": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Your Message"})
        }

class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = PatientRegistration
        fields = [
            'first_name', 'last_name', 'primary_phone', 'alternate_phone',
            'email', 'date_of_birth', 'address', 'ohip_number',
            'current_medications', 'allergies', 'supplements', 'pharmacy_details',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_alternate_phone', 'virtual_care_consent', 'ehr_consent'
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "First Name"}),
            "last_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Last Name"}),
            "primary_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Primary Phone"}),
            "alternate_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Alternate Phone"}),
            "email": forms.EmailInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Email"}),
            "date_of_birth": forms.DateInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "date"}),
            "address": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Address", "rows": 3}),
            "ohip_number": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "OHIP Number"}),
            "current_medications": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Current Medications", "rows": 4}),
            "allergies": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Allergies", "rows": 4}),
            "supplements": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Supplements", "rows": 4}),
            "pharmacy_details": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Pharmacy Details"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Emergency Contact Name"}),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Emergency Contact Phone"}),
            "emergency_contact_alternate_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Emergency Contact Alternate Phone"}),
            "virtual_care_consent": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"}),
            "ehr_consent": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"})
        }


class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        exclude = ['created_at']
        widgets = {
            'name': forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Your Name"}),
            'email': forms.EmailInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Your Email"}),
            'organization': forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Organization Name"}),
            'phone': forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Phone Number (Optional)"}),
            'message': forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "What would you like to see in the demo?", "rows": 3}),
            'preferred_date': forms.DateInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "date"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date to tomorrow
        tomorrow = date.today() + timedelta(days=1)
        self.fields['preferred_date'].widget.attrs['min'] = tomorrow.strftime('%Y-%m-%d')


class ProviderRegistrationForm(forms.Form):
    # Personal Information
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "First Name"}
    ))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "Last Name"}
    ))
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "Email"}
    ))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "Phone Number"}
    ))
    address = forms.CharField(widget=forms.Textarea(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "Address", "rows": 3}
    ))
    
    # Professional Information
    specialty = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "Medical Specialty"}
    ))
    license_number = forms.CharField(max_length=50, required=True, widget=forms.TextInput(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "License Number"}
    ))
    bio = forms.CharField(required=False, widget=forms.Textarea(
        attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
               "placeholder": "Professional Bio (optional)", "rows": 4}
    ))
    
    # Consent
    data_consent = forms.BooleanField(required=True, widget=forms.CheckboxInput(
        attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"}
    ))
    
    # Note: The Practice Details section fields are not included in this form class
    # because they're added directly to the template with plain HTML inputs.
    # If you want to validate these fields, you should add them here as well.

# PATIENT PROFILE EDIT FORM
class PatientProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    primary_phone = forms.CharField(max_length=20, required=True)
    alternate_phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    
    # You can add additional fields as needed
    emergency_contact_name = forms.CharField(max_length=100, required=False)
    emergency_contact_phone = forms.CharField(max_length=20, required=False)

# PROVIDER PROFILE EDIT FORM
class ProviderProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    specialty = forms.CharField(max_length=100, required=True)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    # License number typically should not be editable by the user

class PrescriptionRequestForm(forms.ModelForm):
    class Meta:
        model = PrescriptionRequest
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'ohip_number', 'phone_number',
            'medication_name', 'current_dosage', 'medication_duration', 'last_refill_date',
            'preferred_pharmacy', 'new_medical_conditions', 'new_medications', 'side_effects',
            'information_consent', 'pharmacy_consent'
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "First Name"}),
            "last_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Last Name"}),
            "date_of_birth": forms.DateInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "date"}),
            "ohip_number": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "OHIP Number"}),
            "phone_number": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Phone Number"}),
            "medication_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Medication Name"}),
            "current_dosage": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Current Dosage"}),
            "medication_duration": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "How long have you been taking this medication?"}),
            "last_refill_date": forms.DateInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "date"}),
            "preferred_pharmacy": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Preferred Pharmacy"}),
            "new_medical_conditions": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "List any new medical conditions", "rows": 4}),
            "new_medications": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "List any new medications", "rows": 4}),
            "side_effects": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Describe any side effects or concerns", "rows": 4}),
            "information_consent": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"}),
            "pharmacy_consent": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"})
        }
################################################### MESSAGE FORMS ########################################

class PatientMessageForm(forms.ModelForm):
    """Form for patients to send messages to providers"""
    
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
                "placeholder": "Subject"
            }),
            'content': forms.Textarea(attrs={
                "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm",
                "placeholder": "Your message here",
                "rows": 5
            })
        }

class ProviderMessageForm(forms.ModelForm):
    """Form for providers to send messages to patients"""
    
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'content']
        widgets = {
            'recipient': forms.Select(attrs={
                "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm"
            }),
            'subject': forms.TextInput(attrs={
                "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm",
                "placeholder": "Subject"
            }),
            'content': forms.Textarea(attrs={
                "class": "block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm",
                "placeholder": "Your message here",
                "rows": 5
            })
        }
    
    def __init__(self, *args, **kwargs):
        # Get patients to choose from
        provider = kwargs.pop('provider', None)
        super(ProviderMessageForm, self).__init__(*args, **kwargs)
        
        if provider:
            # In a real implementation, we would filter patients by provider
            from django.contrib.auth.models import User
            from django.db.models import Q
            
            # Get all users that are patients
            patients = User.objects.filter(Q(groups__name='Patient') | Q(is_staff=False, is_superuser=False))
            self.fields['recipient'].queryset = patients
###########################################################################################################
# New forms for the remaining models

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'time', 'type']
        widgets = {
            "doctor": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Doctor Name"}),
            "time": forms.DateTimeInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "datetime-local"}),
            "type": forms.Select(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"}, choices=[('Virtual', 'Virtual'), ('In-Person', 'In-Person')])
        }

# This would be used in provider/admin interfaces


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget that supports multiple file uploads"""
    allow_multiple_selected = True

class MessageForm(forms.ModelForm):
    """Form for creating and sending messages"""
    
    RECIPIENT_TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('staff', 'Staff Member'),
        ('pharmacy', 'Pharmacy'),
        ('billing', 'Billing Department'),
    ]
    
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High Priority'),
    ]
    
    # Fields that aren't in the model or need customization
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50'})
    )
    
    recipient_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    staff_recipient_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        initial='normal',
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'h-4 w-4 text-[#004d40] border-gray-300 focus:ring-[#004d40]'})
    )
    
    add_to_record = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]'})
    )
    
    # Using our custom MultipleFileInput widget instead of ClearableFileInput
    attachments = forms.FileField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt', 'csv', 'xls', 'xlsx']
            )
        ],
        widget=MultipleFileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-md focus:outline-none focus:ring-[#004d40] focus:border-[#004d40]'
        }),
        help_text='You can attach multiple files (max 10MB total)'
    )
    
    thread_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = Message
        fields = ['subject', 'content']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
                'placeholder': 'Message subject'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
                'placeholder': 'Type your message here...',
                'rows': 8
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make all fields required
        for field_name in ['subject', 'content']:
            self.fields[field_name].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        recipient_id = cleaned_data.get('recipient_id')
        staff_recipient_id = cleaned_data.get('staff_recipient_id')
        
        # Check that the appropriate recipient ID is provided
        if recipient_type == 'patient' and not recipient_id:
            self.add_error('recipient_type', "Please select a patient recipient.")
        elif recipient_type == 'staff' and not staff_recipient_id:
            self.add_error('recipient_type', "Please select a staff recipient.")
        
        # Check attachment size
        attachments = self.files.getlist('attachments')
        total_size = sum(attachment.size for attachment in attachments)
        if total_size > 10 * 1024 * 1024:  # 10MB
            self.add_error('attachments', "Total attachment size exceeds 10MB limit.")
        
        return cleaned_data

# For patient use - simpler version that doesn't require selecting sender/recipient
class PatientMessageForm(forms.Form):
    recipient_type = forms.ChoiceField(
        choices=[
            ('provider', 'My Healthcare Provider'),
            ('pharmacy', 'Pharmacy'),
            ('billing', 'Billing Department')
        ],
        widget=forms.Select(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"})
    )
    subject = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Subject"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Your Message", "rows": 4})
    )

# New form for prescription refills
class PrescriptionRefillForm(forms.Form):
    prescription_id = forms.IntegerField(widget=forms.HiddenInput())
    
    # Pharmacy Information
    pharmacy = forms.ChoiceField(
        choices=[
            ('default', 'Northern Pharmacy (Default)'),
            ('other', 'Use a different pharmacy')
        ],
        widget=forms.Select(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"})
    )
    other_pharmacy_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Pharmacy Name"})
    )
    other_pharmacy_address = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Pharmacy Address"})
    )
    other_pharmacy_phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Pharmacy Phone"})
    )
    
    # Additional Information
    last_dose_taken = forms.DateField(
        widget=forms.DateInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "date"})
    )
    medication_changes = forms.ChoiceField(
        choices=[
            ('no', 'No, I\'m taking it as prescribed'),
            ('yes', 'Yes, there have been changes')
        ],
        widget=forms.Select(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"})
    )
    changes_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Describe how your medication regimen has changed", "rows": 3})
    )
    side_effects = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Describe any side effects you've experienced (if none, leave blank)", "rows": 3})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Any additional information you'd like to share", "rows": 3})
    )
    
    # Consent
    information_consent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"})
    )
    pharmacy_consent = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"})
    )

# Provider- ADD PATIENT FORM
class PatientForm(forms.ModelForm):
    class Meta:
        model = PatientRegistration
        fields = [
            'first_name', 'last_name', 'primary_phone', 'alternate_phone',
            'email', 'date_of_birth', 'address', 'ohip_number',
            'current_medications', 'allergies', 'pharmacy_details',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_alternate_phone', 'virtual_care_consent', 'ehr_consent'
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "First Name"}),
            "last_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Last Name"}),
            "primary_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Primary Phone"}),
            "alternate_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Alternate Phone"}),
            "email": forms.EmailInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Email"}),
            "date_of_birth": forms.DateInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "date"}),
            "address": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Address", "rows": 3}),
            "ohip_number": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "OHIP Number"}),
            "current_medications": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Current Medications", "rows": 4}),
            "allergies": forms.Textarea(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Allergies", "rows": 4}),
            "pharmacy_details": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Pharmacy Details"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Emergency Contact Name"}),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Emergency Contact Phone"}),
            "emergency_contact_alternate_phone": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Emergency Contact Alternate Phone"}),
            "virtual_care_consent": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"}),
            "ehr_consent": forms.CheckboxInput(attrs={"class": "h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]"})
        }
