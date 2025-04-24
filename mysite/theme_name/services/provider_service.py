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
