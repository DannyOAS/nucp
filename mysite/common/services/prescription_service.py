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


class PrescriptionService:
    """Service layer for prescription-related operations."""
    
    @staticmethod
    def request_prescription(form_data, request=None):
        """Process a new prescription request."""
        # Save to database
        prescription = PrescriptionRepository.create(form_data)
        
        # Generate PDF
        pdf_result = PrescriptionService.generate_prescription_pdf(form_data)
        
        # Upload to Nextcloud
        if pdf_result['success']:
            cloud_result = PrescriptionService.upload_prescription_to_nextcloud(
                form_data, 
                pdf_result['pdf_data']
            )
        else:
            cloud_result = {'success': False, 'error': 'PDF generation failed'}
        
        # Notify provider (in real implementation)
        # PrescriptionService.notify_provider(prescription)
        
        return {
            'prescription': prescription,
            'pdf_generated': pdf_result['success'],
            'cloud_upload': cloud_result
        }
    
    @staticmethod
    def generate_prescription_pdf(form_data):
        """Generate a PDF for the prescription request."""
        try:
            timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
            
            html_string = render_to_string('prescription_pdf.html', {
                'form_data': form_data,
                'timestamp': timestamp
            })
            
            pdf_file = BytesIO()
            HTML(string=html_string).write_pdf(target=pdf_file)
            
            return {
                'success': True,
                'pdf_data': pdf_file.getvalue()
            }
        except Exception as e:
            logger.error(f"Error generating prescription PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def upload_prescription_to_nextcloud(form_data, pdf_data):
        """Upload prescription PDF to Nextcloud."""
        try:
            patient_name = f"{form_data['first_name']} {form_data['last_name']}"
            folder_name = patient_name.replace(" ", "_")
            username = 'danny'
            password = 'g654D!'  # In production, use environment variables or settings
            base_url = f'https://u3.isnord.ca/remote.php/dav/files/{username}/Patients/Prescriptions/{folder_name}/'
            file_name = 'prescription_request.pdf'
            
            # Create necessary folders
            requests.request('MKCOL', f'https://u3.isnord.ca/remote.php/dav/files/{username}/Patients/Prescriptions/', 
                             auth=(username, password))
            requests.request('MKCOL', base_url, auth=(username, password))
            
            # Upload the PDF
            response = requests.put(
                base_url + file_name,
                data=pdf_data,
                auth=(username, password),
                headers={'Content-Type': 'application/pdf'}
            )
            
            return {
                'success': response.status_code in [200, 201, 204],
                'status_code': response.status_code
            }
        except Exception as e:
            logger.error(f"Error uploading prescription PDF to Nextcloud: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def request_refill(prescription_id, refill_data):
        """Process a prescription refill request."""
        prescription = PrescriptionRepository.get_by_id(prescription_id)
        
        if not prescription:
            return {
                'success': False,
                'error': 'Prescription not found'
            }
        
        # Update refill count and status
        refills_remaining = prescription.get('refills_remaining', 0) - 1
        updated_prescription = PrescriptionRepository.update(
            prescription_id, 
            {'refills_remaining': refills_remaining}
        )
        
        # Generate confirmation
        result = {
            'success': True,
            'prescription': updated_prescription,
            'refill_request_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'estimated_ready_date': datetime.now() + timedelta(days=1)
        }
        
        # In a real implementation, would notify pharmacy
        # PrescriptionService.notify_pharmacy(prescription_id, refill_data)
        
        return result
    
    @staticmethod
    def get_prescriptions_dashboard(patient_id):
        """Get all prescription data needed for prescriptions dashboard."""
        active_prescriptions = PrescriptionRepository.get_active_for_patient(patient_id)
        prescription_history = PrescriptionRepository.get_historical_for_patient(patient_id)
        
        # Calculate additional metrics
        renewal_count = sum(1 for p in active_prescriptions if p.get('status') == 'Renewal Soon')
        
        return {
            'active_prescriptions': active_prescriptions,
            'prescription_history': prescription_history,
            'active_count': len(active_prescriptions),
            'renewal_count': renewal_count
        }

