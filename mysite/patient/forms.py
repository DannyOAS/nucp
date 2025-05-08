from django import forms
from django.core.validators import FileExtensionValidator
from common.models import Message
from patient.models import PrescriptionRequest
from datetime import date

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

# For patient use - simpler version that doesn't require selecting sender/recipient
class SimplePatientMessageForm(forms.Form):
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
