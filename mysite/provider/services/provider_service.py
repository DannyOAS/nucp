# provider/services/provider_service.py
import logging
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.contrib.auth.models import User

from provider.models import Provider
from patient.models import Patient
from common.models import Appointment, Prescription, Message

logger = logging.getLogger(__name__)

class ProviderService:
    """Service layer for provider-related operations."""
    
    @staticmethod
    def get_dashboard_data(provider_id):
        """
        Get dashboard data for a provider including:
        - Recent patients
        - Upcoming appointments
        - Pending prescription requests
        - Stats (today appointments, completed appointments, etc.)
        - AI Scribe data
        - Forms/templates data
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            today = timezone.now().date()
            
            # Get patients for this provider
            patients = Patient.objects.filter(primary_provider=provider).order_by('-user__date_joined')
            
            # Get upcoming appointments
            upcoming_appointments = Appointment.objects.filter(
                doctor=provider,
                time__gte=timezone.now(),
                status='Scheduled'
            ).order_by('time')
            
            # Get pending prescription requests or prescriptions pending renewal
            prescription_requests = Prescription.objects.filter(
                doctor=provider,
                status__in=['Pending', 'Refill Requested']
            ).order_by('-created_at')
            
            # Calculate stats
            stats = {
                'today_appointments': Appointment.objects.filter(
                    doctor=provider,
                    time__date=today
                ).count(),
                'completed_appointments': Appointment.objects.filter(
                    doctor=provider,
                    status='Completed'
                ).count(),
                'active_patients': patients.count(),
                'pending_prescriptions': prescription_requests.count(),
                'unread_messages': Message.objects.filter(
                    recipient=provider.user,
                    status='unread'
                ).count()
            }
            
            # Get AI Scribe data if available
            ai_scribe_data = {}
            try:
                from provider.services import AIScribeService
                ai_scribe_data = AIScribeService.get_recent_scribe_data(provider_id)
            except (ImportError, AttributeError):
                ai_scribe_data = {
                    'enabled': False,
                    'recent_recordings': []
                }
            
            # Get Forms/Templates data if available
            forms_templates_data = {}
            try:
                from provider.services import FormAutomationService
                forms_templates_data = FormAutomationService.get_recent_forms_data(provider_id)
            except (ImportError, AttributeError):
                forms_templates_data = {
                    'enabled': False,
                    'templates': [],
                    'recent_documents': []
                }
            
            return {
                'patients': patients,
                'upcoming_appointments': upcoming_appointments,
                'prescription_requests': prescription_requests,
                'stats': stats,
                'ai_scribe_data': ai_scribe_data,
                'forms_templates_data': forms_templates_data
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'patients': [],
                'upcoming_appointments': [],
                'prescription_requests': [],
                'stats': {
                    'today_appointments': 0,
                    'completed_appointments': 0,
                    'active_patients': 0,
                    'pending_prescriptions': 0,
                    'unread_messages': 0
                },
                'ai_scribe_data': {
                    'enabled': False,
                    'recent_recordings': []
                },
                'forms_templates_data': {
                    'enabled': False,
                    'templates': [],
                    'recent_documents': []
                }
            }
        except Exception as e:
            logger.error(f"Error in get_dashboard_data: {str(e)}")
            raise
    
    @staticmethod
    def update_provider_profile(provider_id, form_data, user):
        """
        Update provider profile information from form data
        Also updates associated user data (first name, last name, email)
        Returns provider dict for template
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Update User fields
            if user:
                user.first_name = form_data.get('first_name', user.first_name)
                user.last_name = form_data.get('last_name', user.last_name)
                user.email = form_data.get('email', user.email)
                user.save()
            
            # Update Provider fields
            provider.license_number = form_data.get('license_number', provider.license_number)
            provider.specialty = form_data.get('specialty', provider.specialty)
            provider.bio = form_data.get('bio', provider.bio)
            provider.phone = form_data.get('phone', provider.phone)
            
            # Save changes
            provider.save()
            
            # Return updated provider dict for template
            provider_dict = {
                'id': provider.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'specialty': provider.specialty,
                'license_number': provider.license_number,
                'bio': provider.bio,
                'phone': provider.phone
            }
            
            return {
                'success': True,
                'provider_dict': provider_dict
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in update_provider_profile: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_provider_settings(provider_id, settings_data):
        """
        Update provider settings like:
        - Notification email
        - SMS/email notification preferences
        - Default appointment duration
        - Calendar sync settings
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Update provider settings fields
            provider.notification_email = settings_data.get('notification_email', provider.notification_email)
            
            # Update boolean flags
            provider.sms_notifications = settings_data.get('sms_notifications', False)
            provider.email_notifications = settings_data.get('email_notifications', True)
            provider.calendar_sync_enabled = settings_data.get('calendar_sync_enabled', False)
            
            # Update integer values
            if 'default_appointment_duration' in settings_data:
                provider.default_appointment_duration = int(settings_data['default_appointment_duration'])
            
            # Save changes
            provider.save()
            
            return {
                'success': True
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in update_provider_settings: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_provider_settings(provider_id):
        """
        Get provider settings including notification preferences
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            settings = {
                'notification_email': getattr(provider, 'notification_email', provider.user.email),
                'sms_notifications': getattr(provider, 'sms_notifications', False),
                'email_notifications': getattr(provider, 'email_notifications', True),
                'default_appointment_duration': getattr(provider, 'default_appointment_duration', 30),
                'calendar_sync_enabled': getattr(provider, 'calendar_sync_enabled', False),
            }
            
            return {
                'success': True,
                'settings': settings
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in get_provider_settings: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_help_support_data():
        """
        Get help/support information including:
        - Support contacts
        - FAQ items
        """
        try:
            from django.conf import settings
            
            # Get support email and phone from settings if available
            support_email = getattr(settings, 'SUPPORT_EMAIL', 'support@northernhealth.ca')
            support_phone = getattr(settings, 'SUPPORT_PHONE', '1-800-555-0100')
            
            # Get FAQ items from database if available, otherwise use default
            faq_items = []
            
            try:
                from common.models import FAQ
                faq_items = list(FAQ.objects.filter(user_type='provider').values('question', 'answer'))
            except (ImportError, AttributeError):
                # Default FAQ items if no FAQ model available
                faq_items = [
                    {
                        'question': 'How do I schedule a new appointment?',
                        'answer': 'Go to the Appointments section and click "Schedule Appointment". Then select a patient, date, and time.'
                    },
                    {
                        'question': 'How do I add a new patient?',
                        'answer': 'Go to the Patients section and click "Add Patient". Fill out the required information and submit the form.'
                    },
                    {
                        'question': 'How do I issue a new prescription?',
                        'answer': 'Go to the Prescriptions section and click "Create Prescription". Select a patient and enter the medication details.'
                    },
                    {
                        'question': 'How do I use the AI scribe feature?',
                        'answer': 'During a video consultation, click "Start Recording" to begin recording. After the session, the AI will generate clinical notes for review.'
                    },
                ]
            
            return {
                'support_email': support_email,
                'support_phone': support_phone,
                'faq_items': faq_items
            }
            
        except Exception as e:
            logger.error(f"Error in get_help_support_data: {str(e)}")
            # Return minimal data on error
            return {
                'support_email': 'support@northernhealth.ca',
                'support_phone': '1-800-555-0100',
                'faq_items': []
            }
