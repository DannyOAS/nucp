# provider/services/patient_service.py
import logging
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta

from provider.models import Provider
from patient.models import Patient
from common.models import Appointment, Prescription, Message

logger = logging.getLogger(__name__)

class PatientService:
    """Service layer for patient-related operations from provider perspective."""
    
    @staticmethod
    def get_provider_patients_dashboard(provider_id, search_query='', filter_type='all'):
        """
        Get patients dashboard data:
        - Filtered and searched patients list
        - Patient stats
        - Recent patient activity
        """
        try:
            # Get provider
            provider = Provider.objects.get(id=provider_id)
            
            # Base queryset - patients where this provider is primary
            patients_queryset = Patient.objects.filter(primary_provider=provider)
            
            # Apply search filter if provided
            if search_query:
                patients_queryset = patients_queryset.filter(
                    Q(user__first_name__icontains=search_query) | 
                    Q(user__last_name__icontains=search_query) |
                    Q(ohip_number__icontains=search_query)
                )
            
            # Apply type filter
            if filter_type == 'recent':
                # Patients with recent activity
                two_weeks_ago = timezone.now() - timedelta(days=14)
                
                # Get patient IDs with recent appointments or prescriptions
                recent_appointment_patients = Appointment.objects.filter(
                    doctor=provider,
                    time__gte=two_weeks_ago
                ).values_list('patient_id', flat=True).distinct()
                
                recent_prescription_patients = Prescription.objects.filter(
                    doctor=provider,
                    created_at__gte=two_weeks_ago
                ).values_list('patient_id', flat=True).distinct()
                
                # Combine the patient IDs
                recent_patient_ids = set(recent_appointment_patients) | set(recent_prescription_patients)
                
                # Filter patients by these IDs
                patients_queryset = patients_queryset.filter(user_id__in=recent_patient_ids)
                
            elif filter_type == 'upcoming':
                # Patients with upcoming appointments
                upcoming_patient_ids = Appointment.objects.filter(
                    doctor=provider,
                    time__gte=timezone.now(),
                    status='Scheduled'
                ).values_list('patient_id', flat=True).distinct()
                
                patients_queryset = patients_queryset.filter(user_id__in=upcoming_patient_ids)
                
            elif filter_type == 'attention':
                # Patients needing attention (pending prescription renewals, upcoming appointments)
                attention_patient_ids = set()
                
                # Patients with pending prescription requests
                prescription_patients = Prescription.objects.filter(
                    doctor=provider,
                    status__in=['Pending', 'Refill Requested']
                ).values_list('patient_id', flat=True).distinct()
                attention_patient_ids.update(prescription_patients)
                
                # Patients with upcoming appointments in next 48 hours
                urgent_appointments = Appointment.objects.filter(
                    doctor=provider,
                    time__gte=timezone.now(),
                    time__lte=timezone.now() + timedelta(hours=48),
                    status='Scheduled'
                ).values_list('patient_id', flat=True).distinct()
                attention_patient_ids.update(urgent_appointments)
                
                patients_queryset = patients_queryset.filter(user_id__in=attention_patient_ids)
            
            # Get recent patient activity
            recent_activity = []
            
            # Recent appointments
            recent_appointments = Appointment.objects.filter(
                doctor=provider
            ).order_by('-time')[:10]
            
            for appointment in recent_appointments:
                if hasattr(appointment, 'patient') and hasattr(appointment.patient, 'get_full_name'):
                    patient_name = appointment.patient.get_full_name()
                else:
                    patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else "Unknown Patient"
                
                recent_activity.append({
                    'type': 'appointment',
                    'patient_id': appointment.patient.id if appointment.patient else None,
                    'patient_name': patient_name,
                    'date': appointment.time,
                    'description': f"Appointment ({appointment.get_status_display()})"
                })
            
            # Recent prescriptions
            recent_prescriptions = Prescription.objects.filter(
                doctor=provider
            ).order_by('-created_at')[:10]
            
            for prescription in recent_prescriptions:
                if hasattr(prescription, 'patient') and hasattr(prescription.patient, 'get_full_name'):
                    patient_name = prescription.patient.get_full_name()
                else:
                    patient_name = f"{prescription.patient.first_name} {prescription.patient.last_name}" if prescription.patient else "Unknown Patient"
                
                recent_activity.append({
                    'type': 'prescription',
                    'patient_id': prescription.patient.id if prescription.patient else None,
                    'patient_name': patient_name,
                    'date': prescription.created_at,
                    'description': f"Prescription: {prescription.medication_name}"
                })
            
            # Sort all activity by date (newest first)
            recent_activity.sort(key=lambda x: x['date'], reverse=True)
            recent_activity = recent_activity[:10]  # Limit to 10 most recent
            
            # Calculate stats
            stats = {
                'total_patients': patients_queryset.count(),
                'appointments_this_week': Appointment.objects.filter(
                    doctor=provider,
                    time__gte=timezone.now(),
                    time__lte=timezone.now() + timedelta(days=7)
                ).count(),
                'requiring_attention': Appointment.objects.filter(
                    doctor=provider,
                    time__gte=timezone.now(),
                    time__lte=timezone.now() + timedelta(hours=48),
                    status='Scheduled'
                ).count() + Prescription.objects.filter(
                    doctor=provider,
                    status__in=['Pending', 'Refill Requested']
                ).count()
            }
            
            return {
                'success': True,
                'patients': patients_queryset,
                'stats': stats,
                'recent_activity': recent_activity
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in get_provider_patients_dashboard: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def add_patient(patient_data, provider_id):
        """
        Add a new patient and set provider as primary provider
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Create User account first
            from django.contrib.auth.models import User
            
            # Check if user with email already exists
            email = patient_data.get('email')
            if User.objects.filter(email=email).exists():
                return {
                    'success': False,
                    'error': f"User with email {email} already exists"
                }
            
            # Generate username from email or names
            if email:
                username = email.split('@')[0]
            else:
                username = f"{patient_data.get('first_name', '').lower()}.{patient_data.get('last_name', '').lower()}"
                
            # Make sure username is unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user object
            user = User.objects.create_user(
                username=username,
                email=email,
                password=User.objects.make_random_password(),  # Generate random password
                first_name=patient_data.get('first_name', ''),
                last_name=patient_data.get('last_name', '')
            )
            
            # Create Patient profile
            patient = Patient.objects.create(
                user=user,
                date_of_birth=patient_data.get('date_of_birth'),
                ohip_number=patient_data.get('ohip_number', ''),
                primary_phone=patient_data.get('primary_phone', ''),
                alternate_phone=patient_data.get('alternate_phone', ''),
                address=patient_data.get('address', ''),
                emergency_contact_name=patient_data.get('emergency_contact_name', ''),
                emergency_contact_phone=patient_data.get('emergency_contact_phone', ''),
                primary_provider=provider
            )
            
            # Handle document upload to cloud if provided in the form
            cloud_upload_result = {'success': True}
            
            if 'documents' in patient_data and hasattr(patient_data['documents'], 'file'):
                try:
                    from common.services.cloud_service import CloudService
                    cloud_upload_result = CloudService.upload_patient_documents(
                        patient_id=patient.id,
                        documents=patient_data['documents']
                    )
                except (ImportError, AttributeError):
                    cloud_upload_result = {
                        'success': False,
                        'error': 'Cloud upload service not available'
                    }
            
            return {
                'success': True,
                'patient_id': patient.id,
                'cloud_upload': cloud_upload_result
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error in add_patient: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_patient_details(patient_id, provider_id):
        """
        Get detailed patient information:
        - Basic patient details
        - Appointments
        - Prescriptions
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            patient = Patient.objects.get(id=patient_id, primary_provider=provider)
            
            # Get upcoming appointments
            upcoming_appointments = Appointment.objects.filter(
                patient=patient.user,
                time__gte=timezone.now()
            ).order_by('time')
            
            # Get past appointments
            past_appointments = Appointment.objects.filter(
                patient=patient.user,
                time__lt=timezone.now()
            ).order_by('-time')[:10]  # Limit to 10 most recent
            
            # Get active prescriptions
            active_prescriptions = Prescription.objects.filter(
                patient=patient.user,
                status='Active'
            ).order_by('-created_at')
            
            # Get historical prescriptions
            historical_prescriptions = Prescription.objects.filter(
                patient=patient.user
            ).exclude(
                status='Active'
            ).order_by('-created_at')[:10]  # Limit to 10 most recent
            
            # Format patient data
            patient_data = {
                'id': patient.id,
                'user_id': patient.user.id,
                'first_name': patient.user.first_name,
                'last_name': patient.user.last_name,
                'email': patient.user.email,
                'date_of_birth': patient.date_of_birth,
                'ohip_number': patient.ohip_number,
                'primary_phone': patient.primary_phone,
                'alternate_phone': patient.alternate_phone,
                'address': patient.address,
                'emergency_contact_name': patient.emergency_contact_name,
                'emergency_contact_phone': patient.emergency_contact_phone
            }
            
            # Get medical history if available
            try:
                medical_history = {}
                if hasattr(patient, 'medical_history'):
                    medical_history = patient.medical_history
                    if not isinstance(medical_history, dict):
                        medical_history = {}
                patient_data['medical_history'] = medical_history
            except AttributeError:
                pass
            
            # Get additional fields if available
            for field in ['allergies', 'current_medications', 'pharmacy_details']:
                if hasattr(patient, field):
                    patient_data[field] = getattr(patient, field)
            
            return {
                'success': True,
                'patient': patient_data,
                'patient_name': f"{patient.user.first_name} {patient.user.last_name}",
                'appointments': upcoming_appointments,
                'past_appointments': past_appointments,
                'prescriptions': active_prescriptions,
                'historical_prescriptions': historical_prescriptions
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Patient.DoesNotExist:
            logger.error(f"Patient with ID {patient_id} not found or not assigned to provider {provider_id}")
            return {
                'success': False,
                'error': 'Patient not found or not assigned to this provider'
            }
        except Exception as e:
            logger.error(f"Error in get_patient_details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
