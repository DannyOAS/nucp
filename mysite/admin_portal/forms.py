from django import forms
from admin_portal.models import AIModelConfig, AIUsageLog

class AIConfigForm(forms.ModelForm):
    """Form for configuring AI models"""
    class Meta:
        model = AIModelConfig
        fields = ['name', 'model_type', 'version', 'api_endpoint', 'configuration_data', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
                'placeholder': 'Model name'
            }),
            'version': forms.TextInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
                'placeholder': 'Version (e.g. 1.0.0)'
            }),
            'api_endpoint': forms.URLInput(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
                'placeholder': 'API endpoint URL'
            }),
            'configuration_data': forms.Textarea(attrs={
                'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
                'placeholder': 'Configuration data in JSON format',
                'rows': 8
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]'
            }),
        }

    def clean_configuration_data(self):
        """Validate that configuration_data is valid JSON"""
        import json
        data = self.cleaned_data['configuration_data']
        try:
            if data:  # Only try to parse if there's data
                json.loads(data)
        except json.JSONDecodeError:
            raise forms.ValidationError("Configuration data must be valid JSON")
        return data

class DocumentTemplateForm(forms.Form):
    """Form for creating and editing document templates"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
            'placeholder': 'Template name'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
            'placeholder': 'Template description',
            'rows': 3
        })
    )
    
    template_type = forms.ChoiceField(
        choices=[
            ('lab_req', 'Lab Requisition'),
            ('sick_note', 'Sick Note'),
            ('referral', 'Referral Letter'),
            ('insurance', 'Insurance Form'),
            ('prescription', 'Prescription Form'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50'
        })
    )
    
    template_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-[#004d40] focus:ring focus:ring-[#004d40] focus:ring-opacity-50',
            'placeholder': 'Template content (HTML format)',
            'rows': 15
        })
    )
    
    requires_patient_data = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]'
        })
    )
    
    requires_provider_data = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]'
        })
    )
    
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-[#004d40] border-gray-300 rounded focus:ring-[#004d40]'
        })
    )
