from django import forms
from django.core.validators import FileExtensionValidator
from common.models import Message

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
