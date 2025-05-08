from django import forms
from .models import ContactMessage, PatientRegistration, DemoRequest
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
