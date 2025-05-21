# patient/services/email_service.py
from common.models import Message
from patient.models import Patient
from django.utils import timezone

class EmailService:
    """Service layer for patient email operations"""
    
    @staticmethod
    def get_email_dashboard(patient_id):
        """
        Get email dashboard data for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing email data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get inbox messages (excluding deleted)
            inbox_messages = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).order_by('-created_at')[:5]  # Limit to 5 most recent
            
            # Get unread count
            unread_count = Message.objects.filter(
                recipient=user,
                status='unread'
            ).count()
            
            # Get read count
            read_count = Message.objects.filter(
                recipient=user,
                status='read'
            ).count()
            
            # Get sent count
            sent_count = Message.objects.filter(
                sender=user
            ).count()
            
            # Get archived count 
            archived_count = Message.objects.filter(
                recipient=user,
                status='archived'
            ).count()
            
            return {
                'success': True,
                'inbox_messages': inbox_messages,
                'unread_count': unread_count,
                'read_count': read_count,
                'sent_count': sent_count,
                'archived_count': archived_count
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'inbox_messages': [],
                'unread_count': 0,
                'read_count': 0,
                'sent_count': 0,
                'archived_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'inbox_messages': [],
                'unread_count': 0,
                'read_count': 0,
                'sent_count': 0,
                'archived_count': 0
            }
    
    @staticmethod
    def get_inbox_messages(patient_id, page=1, page_size=10):
        """
        Get inbox messages with pagination
        
        Args:
            patient_id: ID of the patient
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            dict: Dictionary containing paginated inbox messages
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get inbox messages (excluding deleted)
            all_messages = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).order_by('-created_at')
            
            # Apply pagination
            start = (page - 1) * page_size
            end = start + page_size
            paginated_messages = all_messages[start:end]
            
            return {
                'success': True,
                'messages': paginated_messages,
                'total_count': all_messages.count(),
                'page': page,
                'page_size': page_size,
                'total_pages': (all_messages.count() + page_size - 1) // page_size
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
    
    @staticmethod
    def get_sent_messages(patient_id, page=1, page_size=10):
        """
        Get sent messages with pagination
        
        Args:
            patient_id: ID of the patient
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            dict: Dictionary containing paginated sent messages
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get sent messages
            all_messages = Message.objects.filter(
                sender=user
            ).order_by('-created_at')
            
            # Apply pagination
            start = (page - 1) * page_size
            end = start + page_size
            paginated_messages = all_messages[start:end]
            
            return {
                'success': True,
                'messages': paginated_messages,
                'total_count': all_messages.count(),
                'page': page,
                'page_size': page_size,
                'total_pages': (all_messages.count() + page_size - 1) // page_size
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'messages': [],
                'total_count': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }
    
    @staticmethod
    def compose_email(patient_id, recipient_data, email_data, user):
        """
        Compose and send a new email
        
        Args:
            patient_id: ID of the patient
            recipient_data: Recipient information
            email_data: Email content and subject
            user: User object for sender verification
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Verify user ownership
            if patient.user != user:
                return {
                    'success': False,
                    'error': 'Not authorized to send emails as this patient'
                }
            
            # Extract data
            recipient_type = recipient_data.get('recipient_type')
            subject = email_data.get('subject')
            content = email_data.get('content')
            
            # Validate required fields
            if not all([recipient_type, subject, content]):
                return {
                    'success': False,
                    'error': 'Recipient, subject, and content are required'
                }
            
            # Determine recipient based on type
            recipient = None
            if recipient_type == 'provider' and patient.primary_provider:
                recipient = patient.primary_provider.user
            elif recipient_type == 'pharmacy':
                # This would need to be implemented based on your user model
                from django.contrib.auth.models import Group
                pharmacy_group = Group.objects.filter(name='pharmacy').first()
                if pharmacy_group and pharmacy_group.user_set.exists():
                    recipient = pharmacy_group.user_set.first()
            elif recipient_type == 'billing':
                from django.contrib.auth.models import Group
                billing_group = Group.objects.filter(name='billing').first()
                if billing_group and billing_group.user_set.exists():
                    recipient = billing_group.user_set.first()
            
            if not recipient:
                return {
                    'success': False,
                    'error': f'Could not determine recipient for type: {recipient_type}'
                }
            
            # Create message
            message = Message.objects.create(
                sender=user,
                recipient=recipient,
                subject=subject,
                content=content,
                status='unread',
                sender_type='patient'
            )
            
            return {
                'success': True,
                'message': message
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
