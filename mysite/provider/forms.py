from django import forms
from django.contrib.auth.models import User
from common.models import Appointment, Message
from theme_name.models import PatientRegistration
from .models import Provider, ClinicalNote, DocumentTemplate, GeneratedDocument

class ProviderProfileEditForm(forms.ModelForm):
    """Form for editing provider profile"""
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Provider
        fields = ['specialty', 'bio', 'phone', 'license_number']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'}),
            'specialty': forms.TextInput(attrs={'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'}),
            'phone': forms.TextInput(attrs={'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'}),
            'license_number': forms.TextInput(attrs={'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'})
        }
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            initial = kwargs.get('initial', {})
            initial['first_name'] = instance.user.first_name
            initial['last_name'] = instance.user.last_name
            initial['email'] = instance.user.email
            kwargs['initial'] = initial
        super(ProviderProfileEditForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        provider = super(ProviderProfileEditForm, self).save(commit=False)
        
        # Update the related User model fields
        user = provider.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            provider.save()
        
        return provider

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
            # Get all users that are patients
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
            "time": forms.DateTimeInput(attrs={
                "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline", 
                "type": "datetime-local"
            }),
            "type": forms.Select(attrs={
                "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            }, choices=[('Virtual', 'Virtual'), ('In-Person', 'In-Person')])
        }
    
    def __init__(self, *args, **kwargs):
        provider = kwargs.pop('provider', None)
        super(AppointmentForm, self).__init__(*args, **kwargs)
        
        if provider:
            self.fields['doctor'].initial = provider
            self.fields['doctor'].widget = forms.HiddenInput()

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
    
    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super(PatientForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        """Override save to assign the provider"""
        patient = super(PatientForm, self).save(commit=False)
        
        # Assign provider if available
        if self.provider and hasattr(patient, 'provider'):
            patient.provider = self.provider
        
        if commit:
            patient.save()
            
        return patient

class ClinicalNoteForm(forms.ModelForm):
    class Meta:
        model = ClinicalNote
        fields = ['provider_edited_text', 'status']
        widgets = {
            'provider_edited_text': forms.Textarea(attrs={
                'rows': 10,
                'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'
            }),
            'status': forms.Select(attrs={
                'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'
            })
        }

class DocumentTemplateSelectForm(forms.Form):
    """Form for selecting a document template"""
    template = forms.ModelChoiceField(
        queryset=DocumentTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-[#004d40] focus:border-[#004d40] sm:text-sm'
        })
    )
