# services.py
import json
import os
from django.conf import settings
from datetime import datetime, timedelta
from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML
import requests
import logging
from django.core.mail import send_mail
from django.contrib import messages

from theme_name.repositories import (
    PatientRepository, 
    PrescriptionRepository, 
    AppointmentRepository, 
    MessageRepository, 
    ProviderRepository
)

logger = logging.getLogger(__name__)

# Import models
# In a real implementation, you would uncomment these imports
# from .models import RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument, AIModelConfig, AIUsageLog

class FormAutomationService:
    """Service for automating administrative forms and documents"""
    
    @staticmethod
    def get_available_templates(user_id=None, template_type=None):
        """
        Get available templates, optionally filtered by type
        
        Args:
            user_id: Optional user ID to check permissions
            template_type: Optional template type to filter by
            
        Returns:
            dict: A dictionary with success status and list of available templates
        """
        try:
            templates = [
                {
                    'id': 1,
                    'name': 'Standard Lab Requisition',
                    'template_type': 'lab_req',
                    'description': 'Standard laboratory test requisition form',
                    'requires_patient_data': True,
                    'requires_provider_data': True
                },
                {
                    'id': 2,
                    'name': 'Sick Note - Short Term',
                    'template_type': 'sick_note',
                    'description': 'Short-term sick note for work or school absence',
                    'requires_patient_data': True,
                    'requires_provider_data': True
                },
                {
                    'id': 3,
                    'name': 'Specialist Referral',
                    'template_type': 'referral',
                    'description': 'General specialist referral letter',
                    'requires_patient_data': True,
                    'requires_provider_data': True
                },
                {
                    'id': 4,
                    'name': 'Insurance Form',
                    'template_type': 'insurance',
                    'description': 'Standard insurance claim form',
                    'requires_patient_data': True,
                    'requires_provider_data': True
                },
                {
                    'id': 5,
                    'name': 'Prescription Form',
                    'template_type': 'prescription',
                    'description': 'Standard prescription form',
                    'requires_patient_data': True,
                    'requires_provider_data': True
                },
                {
                    'id': 6,
                    'name': 'Medical Certificate',
                    'template_type': 'certificate',
                    'description': 'Medical certificate for various purposes',
                    'requires_patient_data': True,
                    'requires_provider_data': True
                }
            ]
            
            if template_type:
                templates = [t for t in templates if t['template_type'] == template_type]
            
            logger.info(f"Successfully retrieved {len(templates)} templates")
            
            return {
                'success': True,
                'templates': templates
            }
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'templates': []
            }
    
    @staticmethod
    def get_template_by_id(template_id):
        """
        Get a specific template by ID
        
        Args:
            template_id: The ID of the template to get
            
        Returns:
            dict: The template details
        """
        try:
            templates = FormAutomationService.get_available_templates()
            if not templates['success']:
                return templates
            
            template = next((t for t in templates['templates'] if t['id'] == template_id), None)
            
            if template:
                if template['template_type'] == 'lab_req':
                    template['template_content'] = """
                    <h1>Laboratory Requisition</h1>
                    <div class="patient-info">
                        <h2>Patient Information</h2>
                        <p>Name: {{patient.first_name}} {{patient.last_name}}</p>
                        <p>DOB: {{patient.date_of_birth}}</p>
                        <p>Health Card: {{patient.ohip_number}}</p>
                    </div>
                    <div class="provider-info">
                        <h2>Ordering Provider</h2>
                        <p>Name: {{provider.first_name}} {{provider.last_name}}</p>
                        <p>License: {{provider.license_number}}</p>
                    </div>
                    <div class="tests">
                        <h2>Tests Requested</h2>
                        {% for test in tests %}
                            <div class="test">
                                <input type="checkbox" id="test-{{test.id}}" name="test-{{test.id}}" {% if test.selected %}checked{% endif %}>
                                <label for="test-{{test.id}}">{{test.name}}</label>
                            </div>
                        {% endfor %}
                    </div>
                    """
                
                return {
                    'success': True,
                    'template': template
                }
            else:
                return {
                    'success': False,
                    'error': 'Template not found'
                }
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_document(template_id, form_data, created_by_id):
        """
        Create a new document from a template and form data
        
        Args:
            template_id: The ID of the template to use
            form_data: The form data to populate the template with
            created_by_id: The ID of the user creating the document
            
        Returns:
            dict: Status of the document creation
        """
        try:
            template_result = FormAutomationService.get_template_by_id(template_id)
            if not template_result['success']:
                return template_result
            
            template = template_result['template']
            
            document_data = {
                'id': 1,  # Would be a real ID in actual implementation
                'template_id': template_id,
                'template_name': template['name'],
                'patient_id': form_data.get('patient_id'),
                'patient_name': form_data.get('patient_name', 'John Doe'),
                'created_by_id': created_by_id,
                'status': 'draft',
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'document': document_data
            }
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def render_document(document_id):
        """
        Render a document as HTML and/or PDF
        
        Args:
            document_id: The ID of the document to render
            
        Returns:
            dict: The rendered document
        """
        try:
            html_content = """
            <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        h1 { color: #004d40; }
                        .header { border-bottom: 1px solid #004d40; padding-bottom: 10px; }
                        .patient-info { margin: 20px 0; }
                        .provider-info { margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Laboratory Requisition</h1>
                    </div>
                    
                    <div class="patient-info">
                        <h2>Patient Information</h2>
                        <p>Name: John Doe</p>
                        <p>DOB: 1985-04-12</p>
                        <p>Health Card: 1234567890</p>
                    </div>
                    
                    <div class="provider-info">
                        <h2>Ordering Provider</h2>
                        <p>Name: Dr. James Smith</p>
                        <p>License: MD12345</p>
                    </div>
                    
                    <div class="tests">
                        <h2>Tests Requested</h2>
                        <div class="test">
                            <input type="checkbox" checked> Complete Blood Count (CBC)
                        </div>
                        <div class="test">
                            <input type="checkbox" checked> Comprehensive Metabolic Panel
                        </div>
                        <div class="test">
                            <input type="checkbox"> Lipid Panel
                        </div>
                    </div>
                </body>
            </html>
            """
            
            return {
                'success': True,
                'document_id': document_id,
                'html_content': html_content,
                'pdf_available': True
            }
        except Exception as e:
            logger.error(f"Error rendering document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def auto_populate_form(template_id, patient_id, provider_id=None):
        """
        Auto-populate a form with patient and provider data
        
        Args:
            template_id: The ID of the template to use
            patient_id: The ID of the patient
            provider_id: Optional ID of the provider
            
        Returns:
            dict: Pre-filled form data
        """
        try:
            from datetime import timedelta  # Needed for date arithmetic
            template_result = FormAutomationService.get_template_by_id(template_id)
            if not template_result['success']:
                return template_result
            
            template = template_result['template']
            
            patient_data = {
                'id': patient_id,
                'first_name': 'John',
                'last_name': 'Doe',
                'date_of_birth': '1985-04-12',
                'ohip_number': '1234567890',
                'address': '123 Main St, Toronto, ON',
                'phone': '(555) 123-4567',
                'email': 'john.doe@example.com'
            }
            
            provider_data = None
            if provider_id:
                provider_data = {
                    'id': provider_id,
                    'first_name': 'James',
                    'last_name': 'Smith',
                    'title': 'Dr.',
                    'license_number': 'MD12345',
                    'speciality': 'Family Medicine'
                }
            
            form_data = {'patient': patient_data}
            
            if provider_data:
                form_data['provider'] = provider_data
            
            if template['template_type'] == 'lab_req':
                form_data['tests'] = [
                    {'id': 1, 'name': 'Complete Blood Count (CBC)', 'selected': True},
                    {'id': 2, 'name': 'Comprehensive Metabolic Panel', 'selected': True},
                    {'id': 3, 'name': 'Lipid Panel', 'selected': False},
                    {'id': 4, 'name': 'Thyroid Stimulating Hormone (TSH)', 'selected': False},
                    {'id': 5, 'name': 'Hemoglobin A1C', 'selected': False}
                ]
            elif template['template_type'] == 'sick_note':
                form_data['absence'] = {
                    'start_date': datetime.now().strftime('%Y-%m-%d'),
                    'end_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                    'reason': 'Medical reasons',
                    'restrictions': 'None'
                }
            
            return {
                'success': True,
                'form_data': form_data
            }
        except Exception as e:
            logger.error(f"Error auto-populating form: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
