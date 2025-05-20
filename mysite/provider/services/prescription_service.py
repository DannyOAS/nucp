# provider/services/prescription_service.py
import logging
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta, date

from provider.models import Provider
from patient.models import Patient
from common.models import Prescription

logger = logging.getLogger(__name__)

class PrescriptionService:
    """Service layer for prescription-related operations."""
    
    @staticmethod
    def get_provider_prescriptions_dashboard(provider_id, time_period='week', search_query=''):
        """
        Get prescriptions dashboard data:
        - Recent prescriptions based on time period
        - Prescription requests
        - Stats
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            now = timezone.now()
            
            # Determine date range based on time period
            if time_period == 'day':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == 'week':
                # Start from the beginning of the week (Monday)
                weekday = now.weekday()
                start_date = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == 'month':
                # Start from the 1st of the month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                # Default to week if invalid period
                weekday = now.weekday()
                start_date = (now - timedelta(days=weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get recent prescriptions based on date range and search
            prescriptions_query = Prescription.objects.filter(doctor=provider)
            
            if search_query:
                prescriptions_query = prescriptions_query.filter(
                    Q(medication_name__icontains=search_query) |
                    Q(patient__first_name__icontains=search_query) |
                    Q(patient__last_name__icontains=search_query)
                )
            
            # Apply date filter for 'recent' prescriptions
            recent_prescriptions = prescriptions_query.filter(
                created_at__gte=start_date
            ).order_by('-created_at')
            
            # Get prescription requests (pending prescriptions and refill requests)
            prescription_requests = prescriptions_query.filter(
                status__in=['Pending', 'Refill Requested']
            ).order_by('-created_at')
            
            # Calculate stats
            active_count = prescriptions_query.filter(status='Active').count()
            pending_count = prescriptions_query.filter(status='Pending').count()
            refill_count = prescriptions_query.filter(status='Refill Requested').count()
            
            # Get count created today
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            new_today_count = prescriptions_query.filter(created_at__gte=today_start).count()
            
            stats = {
                'active_prescriptions': active_count,
                'pending_renewals': pending_count,
                'new_today': new_today_count,
                'refill_requests': refill_count,
                'total': prescriptions_query.count()
            }
            
            return {
                'recent_prescriptions': recent_prescriptions,
                'prescription_requests': prescription_requests,
                'stats': stats
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'recent_prescriptions': [],
                'prescription_requests': [],
                'stats': {
                    'active_prescriptions': 0,
                    'pending_renewals': 0,
                    'new_today': 0,
                    'refill_requests': 0,
                    'total': 0
                }
            }
        except Exception as e:
            logger.error(f"Error in get_provider_prescriptions_dashboard: {str(e)}")
            raise
    
    @staticmethod
    def approve_prescription(prescription_id, provider_id):
        """
        Approve a prescription request
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            prescription = Prescription.objects.get(id=prescription_id, doctor=provider)
            
            # Verify the prescription is in a state that can be approved
            if prescription.status not in ['Pending', 'Refill Requested']:
                return {
                    'success': False,
                    'error': f"Cannot approve prescription with status '{prescription.status}'"
                }
            
            # Update status to active
            prescription.status = 'Active'
            
            # If this was a refill request, update refills_remaining
            if prescription.status == 'Refill Requested':
                prescription.refills_remaining = max(0, prescription.refills_remaining - 1)
            
            # Save changes
            prescription.save()
            
            # Send notification if configured
            notification_result = {'success': True}
            try:
                from common.services.notification_service import NotificationService
                notification_result = NotificationService.send_prescription_notification(
                    prescription=prescription,
                    notification_type='approved'
                )
            except (ImportError, AttributeError):
                notification_result = {
                    'success': False,
                    'error': 'Notification service not available'
                }
            
            return {
                'success': True,
                'prescription_id': prescription.id,
                'notification': notification_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Prescription.DoesNotExist:
            logger.error(f"Prescription with ID {prescription_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Prescription not found'
            }
        except Exception as e:
            logger.error(f"Error approving prescription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_prescription_details(prescription_id, provider_id):
        """
        Get detailed info for a single prescription
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            prescription = Prescription.objects.get(id=prescription_id, doctor=provider)
            
            # Get patient details if available
            patient_data = None
            if prescription.patient:
                try:
                    patient = Patient.objects.get(user=prescription.patient)
                    patient_data = {
                        'id': patient.id,
                        'user_id': patient.user.id,
                        'first_name': patient.user.first_name,
                        'last_name': patient.user.last_name,
                        'full_name': f"{patient.user.first_name} {patient.user.last_name}",
                        'email': patient.user.email,
                        'date_of_birth': patient.date_of_birth,
                        'ohip_number': patient.ohip_number
                    }
                except Patient.DoesNotExist:
                    # If patient record not found, use basic user info
                    patient_data = {
                        'user_id': prescription.patient.id,
                        'first_name': prescription.patient.first_name,
                        'last_name': prescription.patient.last_name,
                        'full_name': f"{prescription.patient.first_name} {prescription.patient.last_name}",
                        'email': prescription.patient.email
                    }
            
            return {
                'success': True,
                'prescription': prescription,
                'patient': patient_data
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Prescription.DoesNotExist:
            logger.error(f"Prescription with ID {prescription_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Prescription not found'
            }
        except Exception as e:
            logger.error(f"Error in get_prescription_details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_prescription(prescription_data):
        """
        Create a new prescription
        """
        try:
            # Validate required fields
            required_fields = ['patient_id', 'medication_name', 'dosage', 'doctor_id']
            for field in required_fields:
                if field not in prescription_data or not prescription_data[field]:
                    return {
                        'success': False,
                        'error': f"Field '{field}' is required"
                    }
            
            # Get provider
            try:
                provider = Provider.objects.get(id=prescription_data['doctor_id'])
            except Provider.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Provider not found'
                }
            
            # Get patient
            try:
                patient = Patient.objects.get(id=prescription_data['patient_id'])
                patient_user = patient.user
            except Patient.DoesNotExist:
                try:
                    # Try to get user directly
                    from django.contrib.auth.models import User
                    patient_user = User.objects.get(id=prescription_data['patient_id'])
                except User.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Patient not found'
                    }
            
            # Parse refills
            refills = 0
            try:
                refills = int(prescription_data.get('refills', 0))
            except ValueError:
                refills = 0
            
            # Parse expiration date
            expires = None
            if 'duration' in prescription_data and prescription_data['duration']:
                try:
                    # Try to parse duration as a number of days
                    duration_days = int(prescription_data['duration'])
                    expires = timezone.now().date() + timedelta(days=duration_days)
                except ValueError:
                    # If not a number, check if it's a duration string like "3 months"
                    duration_str = prescription_data['duration'].lower().strip()
                    if 'day' in duration_str:
                        days = int(''.join(filter(str.isdigit, duration_str)))
                        expires = timezone.now().date() + timedelta(days=days)
                    elif 'week' in duration_str:
                        weeks = int(''.join(filter(str.isdigit, duration_str)))
                        expires = timezone.now().date() + timedelta(weeks=weeks)
                    elif 'month' in duration_str:
                        months = int(''.join(filter(str.isdigit, duration_str)))
                        # Approximate months as 30 days
                        expires = timezone.now().date() + timedelta(days=30 * months)
                    elif 'year' in duration_str:
                        years = int(''.join(filter(str.isdigit, duration_str)))
                        # Approximate years as 365 days
                        expires = timezone.now().date() + timedelta(days=365 * years)
            
            # Create the prescription
            prescription = Prescription.objects.create(
                patient=patient_user,
                doctor=provider,
                medication_name=prescription_data['medication_name'],
                dosage=prescription_data['dosage'],
                instructions=prescription_data.get('instructions', ''),
                refills=refills,
                refills_remaining=refills,
                expires=expires,
                status='Active'  # Automatically active since provider is creating it
            )
            
            # Send notification if configured
            notification_result = {'success': True}
            try:
                from common.services.notification_service import NotificationService
                notification_result = NotificationService.send_prescription_notification(
                    prescription=prescription,
                    notification_type='created'
                )
            except (ImportError, AttributeError):
                notification_result = {
                    'success': False,
                    'error': 'Notification service not available'
                }
            
            return {
                'success': True,
                'prescription_id': prescription.id,
                'notification': notification_result
            }
            
        except Exception as e:
            logger.error(f"Error creating prescription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_prescription_form_data(provider_id):
        """
        Get data needed for prescription form:
        - Patients list
        - Common medications list
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get patients assigned to this provider
            patients = Patient.objects.filter(primary_provider=provider)
            
            # Get common medications (either from database or predefined list)
            common_medications = []
            try:
                # Try to get from database if such a model exists
                from common.models import CommonMedication
                medications = CommonMedication.objects.all()
                common_medications = [med.name for med in medications]
            except (ImportError, AttributeError):
                # Use predefined list if model doesn't exist
                common_medications = [
                    'Amoxicillin', 'Lisinopril', 'Metformin', 'Atorvastatin', 
                    'Levothyroxine', 'Amlodipine', 'Metoprolol', 'Omeprazole',
                    'Losartan', 'Gabapentin', 'Hydrochlorothiazide', 'Sertraline',
                    'Simvastatin', 'Hydrocodone', 'Pantoprazole', 'Furosemide'
                ]
            
            return {
                'patients': patients,
                'common_medications': common_medications
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'patients': [],
                'common_medications': []
            }
        except Exception as e:
            logger.error(f"Error in get_prescription_form_data: {str(e)}")
            return {
                'patients': [],
                'common_medications': []
            }
    
    @staticmethod
    def update_prescription(prescription_id, provider_id, updated_data):
        """
        Update an existing prescription
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            prescription = Prescription.objects.get(id=prescription_id, doctor=provider)
            
            # Update basic fields
            if 'medication_name' in updated_data:
                prescription.medication_name = updated_data['medication_name']
            
            if 'dosage' in updated_data:
                prescription.dosage = updated_data['dosage']
            
            if 'instructions' in updated_data:
                prescription.instructions = updated_data['instructions']
            
            # Parse refills
            if 'refills' in updated_data:
                try:
                    refills = int(updated_data['refills'])
                    # Calculate the difference to apply to refills_remaining
                    refill_diff = refills - prescription.refills
                    prescription.refills = refills
                    prescription.refills_remaining = max(0, prescription.refills_remaining + refill_diff)
                except ValueError:
                    pass  # Ignore if not a valid number
            
            # Parse expiration date
            if 'duration' in updated_data and updated_data['duration']:
                try:
                    # Try to parse duration as a number of days
                    duration_days = int(updated_data['duration'])
                    prescription.expires = timezone.now().date() + timedelta(days=duration_days)
                except ValueError:
                    # If not a number, check if it's a duration string like "3 months"
                    duration_str = updated_data['duration'].lower().strip()
                    if 'day' in duration_str:
                        days = int(''.join(filter(str.isdigit, duration_str)))
                        prescription.expires = timezone.now().date() + timedelta(days=days)
                    elif 'week' in duration_str:
                        weeks = int(''.join(filter(str.isdigit, duration_str)))
                        prescription.expires = timezone.now().date() + timedelta(weeks=weeks)
                    elif 'month' in duration_str:
                        months = int(''.join(filter(str.isdigit, duration_str)))
                        # Approximate months as 30 days
                        prescription.expires = timezone.now().date() + timedelta(days=30 * months)
                    elif 'year' in duration_str:
                        years = int(''.join(filter(str.isdigit, duration_str)))
                        # Approximate years as 365 days
                        prescription.expires = timezone.now().date() + timedelta(days=365 * years)
            
            # Save changes
            prescription.save()
            
            # Send notification if configured
            notification_result = {'success': True}
            try:
                from common.services.notification_service import NotificationService
                notification_result = NotificationService.send_prescription_notification(
                    prescription=prescription,
                    notification_type='updated'
                )
            except (ImportError, AttributeError):
                notification_result = {
                    'success': False,
                    'error': 'Notification service not available'
                }
            
            return {
                'success': True,
                'prescription_id': prescription.id,
                'notification': notification_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Prescription.DoesNotExist:
            logger.error(f"Prescription with ID {prescription_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Prescription not found'
            }
        except Exception as e:
            logger.error(f"Error updating prescription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
