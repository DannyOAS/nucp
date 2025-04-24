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


class PatientService:
    """Service layer for patient-related operations."""
    
    @staticmethod
    def register_patient(form_data, request=None, from_provider=False):
        """Register a new patient and handle related operations."""
        # Save to local database
        patient = PatientRepository.create(form_data)
        
        # Upload to Nextcloud - note we always do this now, just with different sources
        patient_name = f"{form_data['first_name']} {form_data['last_name']}"
        source = "provider" if from_provider else "registration"
        cloud_result = PatientService.upload_to_nextcloud(form_data, patient_name, source=source)
        
        # Sync with ERPNext (only if it's not from provider for now, since ERP might need different fields)
        if not from_provider:
            erp_result = PatientService.sync_with_erpnext(form_data, patient)
        else:
            # For provider registrations, we might want to handle ERP differently
            # For now, just return a success message
            erp_result = {'success': True, 'message': 'ERP sync skipped for provider registration'}
        
        return {
            'patient': patient,
            'cloud_upload': cloud_result,
            'erp_sync': erp_result
        }

    @staticmethod
    def upload_to_nextcloud(form_data, patient_name, source="registration"):
        """
        Upload patient information to Nextcloud.

        Args:
            form_data: Patient form data
            patient_name: Formatted patient name
            source: Source of the upload ('registration' or 'provider')
        Returns:
            dict: Upload result
        """
        try:
            USERNAME = 'danny'
            PASSWORD = 'g654D!'  # In production, use environment variables or settings
            ROOT_URL = f'https://u3.isnord.ca/remote.php/dav/files/{USERNAME}/'
            
            # Folder structure
            folder_safe_name = patient_name.replace(" ", "_")
            PATIENTS_FOLDER = ROOT_URL + 'Patients/Registraton/'
            PATIENT_FOLDER = f"{PATIENTS_FOLDER}{folder_safe_name}/"
            
            file_prefix = "provider_registration" if source == "provider" else "registration"
            FILE_NAME = f"{folder_safe_name}_{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            
            # Format form data as readable .txt with more context
            content = f"Patient Registration\n"
            content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"Source: {source.title()}\n"
            content += "\n--- Patient Information ---\n\n"
            content += "\n".join([f"{k}: {v}" for k, v in form_data.items()])

            # Create parent folders
            requests.request('MKCOL', PATIENTS_FOLDER, auth=(USERNAME, PASSWORD))
            requests.request('MKCOL', PATIENT_FOLDER, auth=(USERNAME, PASSWORD))

            # Upload the file
            response = requests.put(
                PATIENT_FOLDER + FILE_NAME,
                data=content.encode('utf-8'),
                auth=(USERNAME, PASSWORD),
                headers={'Content-Type': 'text/plain'}
            )
            

            logger.info(f"Uploaded patient data to Nextcloud for {patient_name}, status: {response.status_code}")

            return {
                'success': response.status_code in [200, 201, 204],
                'status_code': response.status_code,
                'file_path': PATIENT_FOLDER + FILE_NAME
            }
            
        except Exception as e:
            logger.error(f"Error uploading to Nextcloud: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def sync_with_erpnext(form_data, patient):
        """Sync patient data with ERPNext."""
        try:
            from theme_name.integrations.erp_client import ERPNextClient
            
            # Prepare ERPNext payload
            erp_data = {
                'first_name': form_data.get('first_name'),
                'last_name': form_data.get('last_name'),
                'email': form_data.get('email'),
                'primary_phone': form_data.get('primary_phone'),
                'date_of_birth': form_data.get('date_of_birth').strftime('%Y-%m-%d'),
            }
            
            # Send to ERPNext
            client = ERPNextClient()
            erp_response = client.create_patient(erp_data)
            
            erp_patient_id = erp_response.get('data', {}).get('name')
            
            # Update local patient with ERPNext ID
            if erp_patient_id:
                PatientRepository.update(patient['id'], {'erpnext_id': erp_patient_id})
            
            return {
                'success': True,
                'erp_id': erp_patient_id,
                'response': erp_response
            }
            
        except Exception as e:
            logger.error(f"Error syncing with ERPNext: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_dashboard_data(patient_id):
        """Get all data needed for patient dashboard."""
        patient = PatientRepository.get_by_id(patient_id)
        appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
        prescriptions = PrescriptionRepository.get_active_for_patient(patient_id)
        messages = MessageRepository.get_unread_for_patient(patient_id)
        
        return {
            'patient': patient,
            'appointments': appointments[:2],  # Limit to 2 for dashboard
            'prescriptions': prescriptions[:3],  # Limit to 3 for dashboard
            'messages': messages[:2],  # Limit to 2 for dashboard
            'patient_name': f"{patient['first_name']} {patient['last_name']}"
        }
    
    @staticmethod
    def search_patient_records(patient_id, query):
        """Search across all patient records."""
        return PatientRepository.search(patient_id, query)
    
    # Note: The duplicate definition of search_patient_records has been removed.

