# provider/services/form_automation_service.py
import logging
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import json

from provider.models import Provider
from patient.models import Patient

logger = logging.getLogger(__name__)

class FormAutomationService:
    """Service layer for automated form generation and document management."""
    
    @staticmethod
    def get_forms_dashboard_data(provider_id):
        """
        Get forms dashboard data:
        - Templates
        - Patients
        - Recent documents
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get document templates
            templates = []
            try:
                from provider.models import DocumentTemplate
                templates = DocumentTemplate.objects.filter(
                    is_active=True
                ).order_by('name')
            except (ImportError, AttributeError):
                logger.warning("DocumentTemplate model not found")
            
            # Get patients
            patients = Patient.objects.filter(primary_provider=provider)
            
            # Get recent documents
            recent_documents = []
            try:
                from provider.models import GeneratedDocument
                recent_documents = GeneratedDocument.objects.filter(
                    provider=provider
                ).order_by('-created_at')[:10]  # Limit to 10 most recent
            except (ImportError, AttributeError):
                logger.warning("GeneratedDocument model not found")
            
            return {
                'success': True,
                'templates': templates,
                'patients': patients,
                'recent_documents': recent_documents
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in get_forms_dashboard_data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_recent_forms_data(provider_id):
        """
        Get recent forms data for dashboard
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Check if forms functionality is enabled
            is_enabled = True
            
            # Get active templates
            templates = []
            try:
                from provider.models import DocumentTemplate
                templates = DocumentTemplate.objects.filter(
                    is_active=True
                ).order_by('name')[:5]  # Limit to 5 templates
            except (ImportError, AttributeError):
                logger.warning("DocumentTemplate model not found")
                is_enabled = False
            
            # Get recent documents
            recent_documents = []
            try:
                from provider.models import GeneratedDocument
                recent_documents = GeneratedDocument.objects.filter(
                    provider=provider
                ).order_by('-created_at')[:5]  # Limit to 5 most recent
            except (ImportError, AttributeError):
                logger.warning("GeneratedDocument model not found")
                is_enabled = False
            
            return {
                'enabled': is_enabled,
                'templates': templates,
                'recent_documents': recent_documents
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'enabled': False,
                'templates': [],
                'recent_documents': []
            }
        except Exception as e:
            logger.error(f"Error in get_recent_forms_data: {str(e)}")
            return {
                'enabled': False,
                'templates': [],
                'recent_documents': []
            }
    
    @staticmethod
    def get_template_details(provider_id, template_id, for_admin=False):
        """
        Get detailed info for a template
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get template
            try:
                from provider.models import DocumentTemplate
                template = DocumentTemplate.objects.get(id=template_id)
                
                if not template.is_active and not for_admin:
                    return {
                        'success': False,
                        'error': 'Template is not active'
                    }
                
                return {
                    'success': True,
                    'template': template
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'DocumentTemplate model not found'
                }
            except DocumentTemplate.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in get_template_details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_document(provider_id, template_id, form_data, user):
        """
        Create a new document from a template
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get template
            try:
                from provider.models import DocumentTemplate
                template = DocumentTemplate.objects.get(id=template_id)
                
                if not template.is_active:
                    return {
                        'success': False,
                        'error': 'Template is not active'
                    }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'DocumentTemplate model not found'
                }
            except DocumentTemplate.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
            # Get patient if specified
            patient = None
            if 'patient_id' in form_data and form_data['patient_id']:
                try:
                    patient = Patient.objects.get(id=form_data['patient_id'])
                except Patient.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Patient not found'
                    }
            
            # Process form data
            document_data = {}
            for key, value in form_data.items():
                if key not in ['csrfmiddlewaretoken']:
                    document_data[key] = value
            
            # Create document
            try:
                from provider.models import GeneratedDocument
                document = GeneratedDocument.objects.create(
                    template=template,
                    provider=provider,
                    patient=patient,
                    document_data=json.dumps(document_data),
                    status='draft',
                    created_by=user
                )
                
                # Generate initial rendered content using template
                rendered_content = FormAutomationService.render_document_content(
                    template.template_content,
                    document_data,
                    provider=provider,
                    patient=patient
                )
                
                document.rendered_content = rendered_content
                document.save()
                
                return {
                    'success': True,
                    'document_id': document.id
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'GeneratedDocument model not found'
                }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in create_document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def render_document_content(template_content, form_data, provider=None, patient=None):
        """Helper method to render document content using template and form data"""
        # Simple template rendering logic
        rendered_content = template_content
        
        # Replace form field placeholders
        for key, value in form_data.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered_content = rendered_content.replace(placeholder, str(value))
        
        # Replace provider data if available
        if provider:
            provider_data = {
                'provider_name': f"Dr. {provider.user.first_name} {provider.user.last_name}" if provider.user else "",
                'provider_specialty': provider.specialty if hasattr(provider, 'specialty') else "",
                'provider_license': provider.license_number if hasattr(provider, 'license_number') else "",
            }
            
            for key, value in provider_data.items():
                placeholder = f"{{{{ {key} }}}}"
                rendered_content = rendered_content.replace(placeholder, str(value))
        
        # Replace patient data if available
        if patient:
            patient_data = {
                'patient_name': f"{patient.user.first_name} {patient.user.last_name}" if patient.user else "",
                'patient_dob': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else "",
                'patient_ohip': patient.ohip_number if hasattr(patient, 'ohip_number') else "",
            }
            
            for key, value in patient_data.items():
                placeholder = f"{{{{ {key} }}}}"
                rendered_content = rendered_content.replace(placeholder, str(value))
        
        # Replace current date
        rendered_content = rendered_content.replace("{{ current_date }}", datetime.now().strftime('%Y-%m-%d'))
        
        return rendered_content
    
    @staticmethod
    def auto_populate_form(provider_id, template_id, patient_id):
        """
        Auto-populate form data from patient info
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get template
            try:
                from provider.models import DocumentTemplate
                template = DocumentTemplate.objects.get(id=template_id)
            except (ImportError, AttributeError, DocumentTemplate.DoesNotExist):
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
            # Get patient
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Patient not found'
                }
            
            # Create auto-populated form data
            form_data = {
                'patient_id': patient.id,
                'patient_name': f"{patient.user.first_name} {patient.user.last_name}",
                'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else "",
                'ohip_number': patient.ohip_number if hasattr(patient, 'ohip_number') else "",
                'address': patient.address if hasattr(patient, 'address') else "",
                'phone': patient.primary_phone if hasattr(patient, 'primary_phone') else "",
                'current_date': datetime.now().strftime('%Y-%m-%d'),
                'provider_name': f"Dr. {provider.user.first_name} {provider.user.last_name}" if provider.user else "",
            }
            
            return {
                'success': True,
                'form_data': form_data
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in auto_populate_form: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_provider_patients(provider_id):
        """
        Get patients for provider for forms
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            patients = Patient.objects.filter(primary_provider=provider)
            return patients
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error in get_provider_patients: {str(e)}")
            return []
    
    @staticmethod
    def get_document_details(provider_id, document_id):
        """
        Get detailed info for a document
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get document
            try:
                from provider.models import GeneratedDocument
                document = GeneratedDocument.objects.get(id=document_id, provider=provider)
                
                return {
                    'success': True,
                    'document': document
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'GeneratedDocument model not found'
                }
            except GeneratedDocument.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in get_document_details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def render_document(provider_id, document_id):
        """
        Render document as HTML
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get document
            try:
                from provider.models import GeneratedDocument
                document = GeneratedDocument.objects.get(id=document_id, provider=provider)
                
                # Use the already rendered content if available
                if document.rendered_content:
                    html_content = document.rendered_content
                else:
                    # Parse document data
                    try:
                        document_data = json.loads(document.document_data)
                    except json.JSONDecodeError:
                        document_data = {}
                    
                    # Render content using template
                    html_content = FormAutomationService.render_document_content(
                        document.template.template_content,
                        document_data,
                        provider=provider,
                        patient=document.patient
                    )
                    
                    # Save the rendered content
                    document.rendered_content = html_content
                    document.save()
                
                # Check if PDF is available
                pdf_available = bool(document.pdf_storage_path)
                
                return {
                    'success': True,
                    'html_content': html_content,
                    'pdf_available': pdf_available
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'GeneratedDocument model not found'
                }
            except GeneratedDocument.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in render_document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_document_pdf(provider_id, document_id):
        """
        Generate PDF from document
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get document
            try:
                from provider.models import GeneratedDocument
                document = GeneratedDocument.objects.get(id=document_id, provider=provider)
                
                # Get the HTML content
                render_result = FormAutomationService.render_document(provider_id, document_id)
                if not render_result.get('success'):
                    return render_result
                
                html_content = render_result.get('html_content')
                
                # Generate PDF using WeasyPrint if available
                try:
                    from weasyprint import HTML
                    from io import BytesIO
                    
                    # Generate PDF
                    buffer = BytesIO()
                    HTML(string=html_content).write_pdf(buffer)
                    
                    # Save the PDF path if storage is configured
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    
                    pdf_filename = f"document_{document.id}.pdf"
                    pdf_path = f"documents/{provider.id}/{pdf_filename}"
                    
                    # Save to storage
                    default_storage.save(pdf_path, ContentFile(buffer.getvalue()))
                    
                    # Update document with PDF path
                    document.pdf_storage_path = pdf_path
                    document.save()
                    
                    return {
                        'success': True,
                        'pdf_content': buffer.getvalue(),
                        'filename': pdf_filename
                    }
                except ImportError:
                    return {
                        'success': False,
                        'error': 'WeasyPrint or required libraries not available'
                    }
                
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'GeneratedDocument model not found'
                }
            except GeneratedDocument.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in generate_document_pdf: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_document_status(provider_id, document_id, status, user):
        """
        Update document status
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get document
            try:
                from provider.models import GeneratedDocument
                document = GeneratedDocument.objects.get(id=document_id, provider=provider)
                
                # Validate status
                valid_statuses = ['draft', 'final', 'approved', 'sent', 'archived']
                if status not in valid_statuses:
                    return {
                        'success': False,
                        'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                    }
                
                # Update status
                document.status = status
                
                # Update approved_by if status is 'approved'
                if status == 'approved':
                    document.approved_by = user
                
                document.save()
                
                return {
                    'success': True,
                    'document': {
                        'id': document.id,
                        'status': document.status
                    }
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'GeneratedDocument model not found'
                }
            except GeneratedDocument.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Document not found'
                }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in update_document_status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_templates_dashboard_data():
        """
        Get templates dashboard data
        """
        try:
            # Get all templates
            try:
                from provider.models import DocumentTemplate
                templates = DocumentTemplate.objects.all().order_by('name')
                
                return {
                    'success': True,
                    'templates': templates
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'DocumentTemplate model not found'
                }
            
        except Exception as e:
            logger.error(f"Error in get_templates_dashboard_data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_template(template_data, user):
        """
        Create a new template
        """
        try:
            # Validate required fields
            required_fields = ['name', 'template_type', 'template_content']
            for field in required_fields:
                if field not in template_data or not template_data[field]:
                    return {
                        'success': False,
                        'error': f"Field '{field}' is required"
                    }
            
            # Create template
            try:
                from provider.models import DocumentTemplate
                template = DocumentTemplate.objects.create(
                    name=template_data['name'],
                    description=template_data.get('description', ''),
                    template_type=template_data['template_type'],
                    template_content=template_data['template_content'],
                    requires_patient_data=template_data.get('requires_patient_data', False),
                    requires_provider_data=template_data.get('requires_provider_data', False),
                    is_active=template_data.get('is_active', True),
                    created_by=user
                )
                
                return {
                    'success': True,
                    'template_id': template.id
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'DocumentTemplate model not found'
                }
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_template(template_id, update_data, user):
        """
        Update an existing template
        """
        try:
            # Get template
            try:
                from provider.models import DocumentTemplate
                template = DocumentTemplate.objects.get(id=template_id)
                
                # Update fields
                if 'name' in update_data:
                    template.name = update_data['name']
                
                if 'description' in update_data:
                    template.description = update_data['description']
                
                if 'template_type' in update_data:
                    template.template_type = update_data['template_type']
                
                if 'template_content' in update_data:
                    template.template_content = update_data['template_content']
                
                if 'requires_patient_data' in update_data:
                    template.requires_patient_data = update_data['requires_patient_data']
                
                if 'requires_provider_data' in update_data:
                    template.requires_provider_data = update_data['requires_provider_data']
                
                if 'is_active' in update_data:
                    template.is_active = update_data['is_active']
                
                template.save()
                
                return {
                    'success': True,
                    'template_id': template.id
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'DocumentTemplate model not found'
                }
            except DocumentTemplate.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Template not found'
                }
            
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
