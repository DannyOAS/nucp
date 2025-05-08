from django import forms
from common.models import Appointment, Message
from theme_name.models import PatientRegistration

class ProviderProfileEditForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)
    specialty = forms.CharField(max_length=100, required=True)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    # License number typically should not be editable by the user

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

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'time', 'type']
        widgets = {
            "doctor": forms.TextInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "placeholder": "Doctor Name"}),
            "time": forms.DateTimeInput(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", "type": "datetime-local"}),
            "type": forms.Select(attrs={"class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"}, choices=[('Virtual', 'Virtual'), ('In-Person', 'In-Person')])
        }

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
