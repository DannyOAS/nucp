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

from .repositories import (
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


class AppointmentService:
    """Service layer for appointment-related operations."""
    
    @staticmethod
    def get_appointments_dashboard(patient_id):
        """Get all appointment data needed for appointments dashboard."""
        upcoming_appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
        past_appointments = AppointmentRepository.get_past_for_patient(patient_id)
        
        # Calculate counts
        upcoming_count = len(upcoming_appointments)
        past_count = len(past_appointments)
        provider_count = len(set([a.get('doctor', '') for a in upcoming_appointments + past_appointments]))
        
        return {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'upcoming_count': upcoming_count,
            'past_count': past_count,
            'provider_count': provider_count
        }
    
    @staticmethod
    def schedule_appointment(appointment_data):
        """Schedule a new appointment."""
        # In a real implementation, this would check for conflicts, etc.
        appointment = AppointmentRepository.create(appointment_data)
        
        # Would send confirmation email in real implementation
        # AppointmentService.send_confirmation_email(appointment)
        
        return appointment
    
    @staticmethod
    def reschedule_appointment(appointment_id, new_time_data):
        """Reschedule an existing appointment."""
        appointment = AppointmentRepository.get_by_id(appointment_id)
        
        if not appointment:
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        
        # Update appointment time
        updated_appointment = AppointmentRepository.update(
            appointment_id, 
            {'time': new_time_data.get('time')}
        )
        
        # Would send update email in real implementation
        # AppointmentService.send_update_email(updated_appointment)
        
        return {
            'success': True,
            'appointment': updated_appointment
        }


class MessageService:
    """Service layer for message-related operations."""
    
    @staticmethod
    def get_message_dashboard(patient_id):
        """Get all message data needed for email dashboard."""
        unread_messages = MessageRepository.get_unread_for_patient(patient_id)
        read_messages = MessageRepository.get_read_for_patient(patient_id)
        
        # These would come from the database in a real implementation
        sent_count = 8  # Sample data
        archived_count = 3  # Sample data
        
        return {
            'unread_messages': unread_messages,
            'read_messages': read_messages,
            'unread_count': len(unread_messages),
            'read_count': len(read_messages),
            'sent_count': sent_count,
            'archived_count': archived_count
        }
    
    @staticmethod
    def send_message(message_data):
        """Send a new message."""
        message = MessageRepository.create(message_data)
        
        # In a real implementation, might send notification
        # MessageService.send_notification(message)
        
        return message
    
    @staticmethod
    def mark_as_read(message_id):
        """Mark a message as read."""
        message = MessageRepository.get_by_id(message_id)
        
        if not message:
            return {
                'success': False,
                'error': 'Message not found'
            }
        
        updated_message = MessageRepository.update(
            message_id, 
            {'read': True}
        )
        
        return {
            'success': True,
            'message': updated_message
        }


class JitsiService:
    """Service layer for Jitsi video consultations."""
    
    @staticmethod
    def get_video_dashboard(patient_id):
        """Get all data needed for Jitsi video dashboard."""
        all_appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
        video_appointments = [a for a in all_appointments if a.get('type') == 'Virtual']
        
        return {
            'video_appointments': video_appointments,
            'upcoming_count': len(video_appointments)
        }
    
    @staticmethod
    def generate_meeting_link(appointment_id):
        """Generate a Jitsi meeting link for an appointment."""
        appointment = AppointmentRepository.get_by_id(appointment_id)
        
        if not appointment:
            return {
                'success': False,
                'error': 'Appointment not found'
            }
        
        # In a real implementation, this would generate a secure meeting link
        meeting_id = f"northernhealth-{appointment_id}-{int(datetime.now().timestamp())}"
        meeting_link = f"https://meet.jit.si/{meeting_id}"
        
        # Update the appointment with the meeting link
        updated_appointment = AppointmentRepository.update(
            appointment_id, 
            {'meeting_link': meeting_link}
        )
        
        return {
            'success': True,
            'meeting_link': meeting_link,
            'appointment': updated_appointment
        }

class ProviderService:
    """Service layer for provider-related operations."""
    
    @staticmethod
    def get_dashboard_data(provider_id):
        """Get all data needed for provider dashboard."""
        provider = ProviderRepository.get_by_id(provider_id)
        
        if not provider:
            provider = {
                'id': provider_id,
                'first_name': 'Default',
                'last_name': 'Provider',
                'title': 'Dr.',
                'specialty': 'Family Medicine'
            }

        # Use existing repositories to get data
        patients = ProviderRepository.get_patients(provider_id)
        appointments = ProviderRepository.get_appointments(provider_id)
        prescription_requests = ProviderRepository.get_prescription_requests(provider_id)
        ######################
        # The block below is now properly indented within the method:
        ai_scribe_data = ProviderService._get_recent_recordings(provider_id)
        # Calculate counts for stats using existing data
        today_appointments = [a for a in appointments if 'today' in a.get('time', '').lower()]
        completed_appointments = [a for a in appointments if a.get('status') == 'Completed']
        active_patients = len(patients)
        
        # Use MessageRepository if available for unread messages
        # For now, just use a count from the existing data
        unread_messages = 7  # This should ideally come from MessageRepository
        
        # Get AI Scribe data from the existing AIScribeService if available
        try:
            from .services import AIScribeService
            ai_scribe_data = {
                'enabled': True,
                'recent_recordings': AIScribeService._get_recent_recordings(provider_id)
            }
        except (ImportError, AttributeError):
            ai_scribe_data = {
                'enabled': True,
                'recent_recordings': []
            }
        
        # Get Forms & Templates data from the appropriate service
        try:
            from .services import FormAutomationService
            forms_result = FormAutomationService.get_available_templates(provider_id)
            forms_templates_data = {
                'enabled': True,
                'templates': forms_result.get('templates', []),
                'recent_documents': []  # This would come from a repository method
            }
        except (ImportError, AttributeError):
            forms_templates_data = {
                'enabled': True,
                'templates': [],
                'recent_documents': []
            }
        
        return {
            'provider': provider,
            'provider_name': f"Dr. {provider['last_name']}",
            'patients': patients[:5],  # Limit to 5 for dashboard
            'appointments': appointments[:3],  # Limit to 3 for dashboard
            'prescription_requests': prescription_requests,
            'stats': {
                'today_appointments': len(today_appointments),
                'completed_appointments': len(completed_appointments),
                'active_patients': active_patients,
                'pending_prescriptions': len(prescription_requests),
                'unread_messages': unread_messages
            },
            'ai_scribe_data': ai_scribe_data,
            'forms_templates_data': forms_templates_data
        }

    @staticmethod
    def get_patients_dashboard(provider_id):
        """Get patient data for the patients dashboard."""
        patients = ProviderRepository.get_patients(provider_id)
        
        # Calculate stats
        total_patients = len(patients)
        appointments_this_week = 18  # Mock count - would be calculated from appointments
        requiring_attention = 5  # Mock count - would be identified with specific criteria
        
        # Get recent activity - in a real implementation would use a dedicated repository
        recent_activity = [
            {
                'type': 'appointment',
                'patient_name': 'Jane Doe',
                'action': 'Completed appointment',
                'time': '1 hour ago'
            },
            {
                'type': 'lab',
                'patient_name': 'John Smith',
                'action': 'New lab results',
                'time': '3 hours ago'
            },
            {
                'type': 'prescription',
                'patient_name': 'Robert Johnson',
                'action': 'Prescription renewal request',
                'time': 'Yesterday'
            },
            {
                'type': 'message',
                'patient_name': 'Emily Williams',
                'action': 'New message',
                'time': '2 days ago'
            }
        ]
        
        return {
            'patients': patients,
            'stats': {
                'total_patients': total_patients,
                'appointments_this_week': appointments_this_week,
                'requiring_attention': requiring_attention
            },
            'recent_activity': recent_activity
        }
    
    @staticmethod
    def get_appointments_dashboard(provider_id):
        """Get appointment data for appointments dashboard."""
        appointments = ProviderRepository.get_appointments(provider_id)
        
        # Separate by status
        today_appointments = [a for a in appointments if 'today' in a.get('time', '').lower()]
        completed = [a for a in appointments if a.get('status') == 'Completed']
        upcoming = [a for a in appointments if a.get('status') != 'Completed' and 'today' not in a.get('time', '').lower()]
        cancelled = []  # Mock - would be filtered in a real implementation
        
        return {
            'appointments': appointments,
            'today_appointments': today_appointments,
            'stats': {
                'today': len(today_appointments),
                'completed': len(completed),
                'upcoming': len(upcoming),
                'cancelled': len(cancelled)
            }
        }
    
    @staticmethod
    def get_prescriptions_dashboard(provider_id, time_period='week', search_query=''):
        """Get prescriptions data for prescriptions dashboard.
    
        Args:
            provider_id: The ID of the provider requesting the dashboard
            time_period: 'today', 'week', or 'month'
            search_query: Optional search query to filter prescriptions
            
        Returns:
            dict: A dictionary containing prescription dashboard data
        """
#        try:
#            from datetime import datetime, timedelta
           # from datetime import date  # For type checking in prescriptions below
#            prescription_requests = ProviderRepository.get_prescription_requests(provider_id)
        
            # Filter by search query if provided
#            if search_query:
#                prescription_requests = [
#                    req for req in prescription_requests 
#                    if (search_query.lower() in req.get('patient_name', '').lower() or 
#                        search_query.lower() in req.get('medication_name', '').lower())
#                ]
        
            # Get current date for filtering
#            today = datetime.now().date()
        
            # Define the time range based on period
#            if time_period == 'today':
#                start_date = today
#            elif time_period == 'week':
#                start_date = today - timedelta(days=7)
#            elif time_period == 'month':
#                start_date = today - timedelta(days=30)
#            else:
#                start_date = today - timedelta(days=7)
#                time_period = 'week'
        
            # Get prescriptions - in a real implementation, would get from repository filtering by date range
#            recent_prescriptions = []
        try:
            print("DEBUG SERVICE - Starting method")
            from datetime import datetime, timedelta, date
        
            # Get prescription requests
            prescription_requests = ProviderRepository.get_prescription_requests(provider_id)
            print(f"DEBUG SERVICE - Got {len(prescription_requests)} prescription requests")
        
            # Get current date for filtering
            today = datetime.now().date()
            print(f"DEBUG SERVICE - Today's date: {today}")
        
            # Define time range
            if time_period == 'today':
                start_date = today
            elif time_period == 'week':
                start_date = today - timedelta(days=7)
            elif time_period == 'month':
                start_date = today - timedelta(days=30)
            else:
                start_date = today - timedelta(days=7)
                time_period = 'week'
            print(f"DEBUG SERVICE - Using time period: {time_period}, start date: {start_date}")
            
            # Mock recent prescriptions
            all_recent_prescriptions = [
                {
                    'id': 1,
                    'date': 'Today',
                    'time': '9:15 AM',
                    'patient_name': 'Robert Johnson',
                    'medication': 'Amoxicillin',
                    'medication_type': 'Antibiotics',
                    'dosage': '500mg, 3 times daily',
                    'duration': 'For 10 days',
                    'refills': '0',
                    'pharmacy': 'Northern Pharmacy',
                    'created_at': today
                },
                {
                    'id': 2,
                    'date': 'Today',
                    'time': '11:30 AM',
                    'patient_name': 'Jane Doe',
                    'medication': 'Sertraline',
                    'medication_type': 'SSRI',
                    'dosage': '50mg, once daily',
                    'duration': '',
                    'refills': '3',
                    'pharmacy': 'Northern Pharmacy',
                    'created_at': today
                },
                {
                    'id': 3,
                    'date': 'Yesterday',
                    'time': '3:45 PM',
                    'patient_name': 'John Smith',
                    'medication': 'Atorvastatin',
                    'medication_type': 'Statin',
                    'dosage': '20mg, once daily',
                    'duration': '',
                    'refills': '5',
                    'pharmacy': 'City Drugs',
                    'created_at': today - timedelta(days=1)
                },
                {
                    'id': 4,
                    'date': '3 days ago',
                    'time': '10:15 AM',
                    'patient_name': 'Emily Williams',
                    'medication': 'Albuterol',
                    'medication_type': 'Inhaler',
                    'dosage': '2 puffs as needed',
                    'duration': '',
                    'refills': '2',
                    'pharmacy': 'Northern Pharmacy',
                    'created_at': today - timedelta(days=3)
                },
                {
                    'id': 5,
                    'date': '5 days ago',
                    'time': '2:00 PM',
                    'patient_name': 'Robert Johnson',
                    'medication': 'Omeprazole',
                    'medication_type': 'PPI',
                    'dosage': '40mg, once daily',
                    'duration': '',
                    'refills': '2',
                    'pharmacy': 'Northern Pharmacy',
                    'created_at': today - timedelta(days=5)
                },
                {
                    'id': 6,
                    'date': '2 weeks ago',
                    'time': '1:30 PM',
                    'patient_name': 'Michael Brown',
                    'medication': 'Metformin',
                    'medication_type': 'Diabetes',
                    'dosage': '500mg twice daily',
                    'duration': '',
                    'refills': '3',
                    'pharmacy': 'City Drugs',
                    'created_at': today - timedelta(days=14)
                }
            ]
            print(f"DEBUG SERVICE - Created {len(all_recent_prescriptions)} mock prescriptions")
            
            # Filter prescriptions based on time period
            recent_prescriptions = []
            for prescription in all_recent_prescriptions:
                try:
                    prescription_date = today  # Default to today
                
                    if isinstance(prescription.get('created_at'), (datetime, date)):
                       prescription_date = prescription['created_at'] if isinstance(prescription['created_at'], date) else prescription['created_at'].date()

                    print(f"DEBUG SERVICE - Checking prescription: {prescription.get('id')}, date: {prescription_date}")
  
                # Apply the time period filter
                    if prescription_date >= start_date:
                        recent_prescriptions.append(prescription)
                except Exception as e:
                    print(f"DEBUG SERVICE - Error processing prescription {prescription.get('id')}: {e}")

            print(f"DEBUG SERVICE - Filtered to {len(recent_prescriptions)} recent prescriptions")
            # Sort by date (newest first)
#            recent_prescriptions.sort(key=lambda x: x.get('created_at', today), reverse=True)
        
            # Calculate stats
                    # Calculate stats
            active_prescriptions = 87
            pending_renewals = len(prescription_requests)
            new_today = sum(1 for p in recent_prescriptions 
                            if isinstance(p.get('created_at'), (datetime, date)) 
                            and (p['created_at'].date() if isinstance(p['created_at'], datetime) else p['created_at']) == today)
            refill_requests = 8
        
            print(f"DEBUG SERVICE - Calculated stats: active={active_prescriptions}, pending={pending_renewals}, new={new_today}, refills={refill_requests}")
        
        
             
            return {
                'prescription_requests': prescription_requests,
                'recent_prescriptions': recent_prescriptions,
                'stats': {
                    'active_prescriptions': active_prescriptions,
                    'pending_renewals': pending_renewals,
                    'new_today': new_today,
                    'refill_requests': refill_requests
                }
            }
        except Exception as e:
            print(f"DEBUG SERVICE - MAJOR ERROR: {e}")
    #        logger.error(f"Error getting prescriptions dashboard: {str(e)}", exc_info=True)
        #Log the full error for debugging
        import traceback
        traceback.print_exc()

        # Return empty data as fallback
        return {
                'prescription_requests': [],
                'recent_prescriptions': [],
                'stats': {
                    'active_prescriptions': 0,
                    'pending_renewals': 0,
                    'new_today': 0,
                    'refill_requests': 0
                },
                'error': str(e)
            }

    @staticmethod
    def get_recent_patient_activity(provider_id):
        """Get recent patient activity for a provider."""
        # In a real implementation, this would query a dedicated activity log
        # For now, return mock data that approximates what would be in the database
    
        # Here's a placeholder implementation - in production this would be database-backed
        return [
            {
                'type': 'appointment',
                'patient_name': 'Jane Doe',
                'action': 'Completed appointment',
                'time': '1 hour ago',
                'timestamp': datetime.now() - timedelta(hours=1)
            },
            {
                'type': 'lab',
                'patient_name': 'John Smith',
                'action': 'New lab results',
                'time': '3 hours ago',
                'timestamp': datetime.now() - timedelta(hours=3)
            },
            {
                'type': 'prescription',
                'patient_name': 'Robert Johnson',
                'action': 'Prescription renewal request',
                'time': 'Yesterday',
                'timestamp': datetime.now() - timedelta(days=1)
            },
            {
                'type': 'message',
                'patient_name': 'Emily Williams',
                'action': 'New message',
                'time': '2 days ago',
                'timestamp': datetime.now() - timedelta(days=2)
            }
        ]

    @staticmethod
    def get_messages_dashboard(provider_id):
        """Get message data for messages dashboard."""
        # Mock messages - in a real implementation would come from MessageRepository
        messages = [
            {
                'id': 1,
                'patient': {
                    'name': 'Jane Doe',
                    'initials': 'JD'
                },
                'subject': 'Prescription question',
                'content': 'I had a question about the side effects of the new medication you prescribed yesterday...',
                'timestamp': 'Today, 10:30 AM',
                'read': False
            },
            {
                'id': 2,
                'patient': {
                    'name': 'John Smith',
                    'initials': 'JS'
                },
                'subject': 'Blood test results',
                'content': 'Thank you for sending my lab results. I have a few questions about the cholesterol numbers...',
                'timestamp': 'Yesterday',
                'read': True
            }
        ]
        
        # Calculate stats
        inbox_count = 24  # Mock count
        unread_count = 8  # Mock count
        awaiting_reply = 5  # Mock count
        today_count = 12  # Mock count
        
        return {
            'messages': messages,
            'stats': {
                'inbox': inbox_count,
                'unread': unread_count,
                'awaiting_reply': awaiting_reply,
                'today': today_count
            }
        }

    @staticmethod
    def _get_recent_recordings(provider_id):
        """Get recent recording sessions for a provider."""
        # In a real implementation, this would query the database for recordings
        # For now, return mock data that matches the structure expected by the dashboard
        return [
            {
                'id': 1,
                'patient_name': 'Jane Doe',
                'appointment_type': 'Annual Checkup',
                'date': 'Today, 9:30 AM',
                'duration': '45 minutes',
                'status': 'Completed'
            },
            {
                'id': 2,
                'patient_name': 'John Smith',
                'appointment_type': 'Follow-up',
                'date': 'Today, 11:00 AM',
                'duration': '30 minutes',
                'status': 'Scheduled'
            }
        ]


class AIScribeService:
    """Service for AI transcription and clinical note generation"""
    
    @staticmethod
    def start_recording(appointment_id):
        """
        Start a recording session for an appointment
        
        Args:
            appointment_id: The ID of the appointment to record
            
        Returns:
            dict: Status of the recording session creation
        """
        try:
            # In a real implementation, would create a RecordingSession object
            # and connect to Jitsi API to start recording
            
            # Mock implementation
            recording_data = {
                'id': 1,  # Would be a real ID in actual implementation
                'appointment_id': appointment_id,
                'jitsi_recording_id': f"jitsi-{appointment_id}-{int(datetime.now().timestamp())}",
                'start_time': datetime.now().isoformat(),
                'status': 'recording'
            }
            
            logger.info(f"Started recording for appointment {appointment_id}")
            
            return {
                'success': True,
                'recording': recording_data
            }
        except Exception as e:
            logger.error(f"Error starting recording: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def stop_recording(recording_id):
        """
        Stop an active recording session
        
        Args:
            recording_id: The ID of the recording to stop
            
        Returns:
            dict: Status of the recording session stop
        """
        try:
            # In a real implementation, would update the RecordingSession
            # and call Jitsi API to stop recording
            
            # Mock implementation
            recording_data = {
                'id': recording_id,
                'end_time': datetime.now().isoformat(),
                'status': 'completed',
                'storage_path': f"/recordings/{recording_id}.mp4"
            }
            
            transcription_task = AIScribeService.process_transcription(recording_id)
            
            return {
                'success': True,
                'recording': recording_data,
                'transcription_status': 'initiated'
            }
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def process_transcription(recording_id):
        """
        Process a recording for transcription
        
        Args:
            recording_id: The ID of the recording to transcribe
            
        Returns:
            dict: Status of the transcription process
        """
        try:
            llm_response = AIScribeService._call_llm_api(
                endpoint="transcribe",
                payload={
                    "recording_id": recording_id,
                    "language": "en-US",
                    "format": "detailed"
                }
            )
            
            transcription_text = llm_response.get('transcription', 'No transcription available')
            
            return {
                'success': True,
                'recording_id': recording_id,
                'transcription_status': 'completed',
                'transcription_text': transcription_text[:100] + '...'
            }
        except Exception as e:
            logger.error(f"Error processing transcription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_clinical_notes(transcription_id):
        """
        Generate clinical notes from a transcription
        
        Args:
            transcription_id: The ID of the transcription
            
        Returns:
            dict: The generated clinical notes
        """
        try:
            transcription_text = (
                "Patient presents with complaints of headache and fatigue for the past week. "
                "No fever or other symptoms. Has history of migraines. Current medication includes..."
            )
            
            llm_response = AIScribeService._call_llm_api(
                endpoint="generate_notes",
                payload={
                    "transcription_text": transcription_text,
                    "format": "SOAP",
                    "include_diagnosis_codes": True
                }
            )
            
            clinical_note = llm_response.get('clinical_note', 'No clinical note generated')
            
            return {
                'success': True,
                'transcription_id': transcription_id,
                'clinical_note': clinical_note[:100] + '...'
            }
        except Exception as e:
            logger.error(f"Error generating clinical notes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _call_llm_api(endpoint, payload):
        """
        Helper method to call the LLM API
        
        Args:
            endpoint: The API endpoint to call
            payload: The payload to send
            
        Returns:
            dict: The API response
        """
        try:
            base_url = getattr(settings, 'LLM_API_URL', 'http://localhost:8000/api/')
            api_key = getattr(settings, 'LLM_API_KEY', 'mock-api-key')
            
            logger.info(f"Calling LLM API endpoint: {endpoint}")
            
            if endpoint == "transcribe":
                return {
                    "success": True,
                    "transcription": (
                        "Patient: I've been having these headaches for about a week now.\n"
                        "Doctor: Can you describe the pain?\n"
                        "Patient: It's a throbbing pain, mainly on the right side..."
                    ),
                    "confidence": 0.92,
                    "language_detected": "en-US",
                    "duration_seconds": 528
                }
            elif endpoint == "generate_notes":
                return {
                    "success": True,
                    "clinical_note": (
                        "SUBJECTIVE:\nPatient presents with complaints of headache and fatigue for the past week. "
                        "Describes the pain as throbbing, mainly on the right side of the head.\n\n"
                        "OBJECTIVE:\nVital signs stable. No fever. No neck stiffness or neurological deficits.\n\n"
                        "ASSESSMENT:\nMigraine headache, consistent with patient's history.\n\n"
                        "PLAN:\n1. Continue current medication.\n2. Increase water intake.\n3. Follow up in 2 weeks if symptoms persist."
                    ),
                    "diagnosis_codes": [
                        "G43.909: Migraine, unspecified, not intractable, without status migrainosus"
                    ],
                    "confidence": 0.88
                }
            else:
                return {
                    "success": False,
                    "error": "Unknown endpoint"
                }
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


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


class AIConfigurationService:
    """Service for managing AI configuration and settings"""

    @staticmethod
    def get_system_status():
        """
        Retrieve the current system status for the AI configuration.
        
        Returns:
            dict: A dictionary containing system status information.
        """
        from datetime import datetime
        return {
            'success': True,
            'status': 'operational',
            'last_updated': datetime.now().isoformat()
        }
    
    @staticmethod
    def get_ai_server_status():
        """Get the status of AI servers"""
        return {
            'success': True,
            'status': 'online',
            'server_ip': '192.168.1.101',
            'api_version': 'v1.2.3',
            'active_connections': 17,
            'response_time': '156ms'
        }
    
    @staticmethod
    def restart_ai_server():
        """Restart AI server"""
        return {
            'success': True,
            'message': 'AI server restarted successfully'
        }

    @staticmethod
    def get_active_model_configs():
        """
        Retrieve a list of active AI model configurations.
    
        Returns:
            dict: A dictionary containing status and a list of active model configurations.
        """
        try:
            return {
                'success': True,
                'models': [
                    {
                        'id': 1,
                        'name': 'ClinicalNoteGenerator-v1',
                        'description': 'Generates SOAP-format clinical notes from transcriptions',
                        'active': True
                    },
                    {
                        'id': 2,
                        'name': 'PrescriptionAssistant-v2',
                        'description': 'Assists in generating prescription recommendations',
                        'active': True
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error retrieving active model configs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
