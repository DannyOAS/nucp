# patient/services/email_service.py
from common.models import Message
from patient.models import Patient
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service layer for patient email operations - OPTIMIZED"""
    
    @staticmethod
    def get_email_dashboard(patient_id):
        """
        OPTIMIZED: Get email data with efficient queries and minimal database hits
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing email data
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Get inbox messages with sender info in single query
            inbox_messages = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).select_related(
                'sender'  # Join sender user data
            ).order_by('-created_at')[:5]
            
            # OPTIMIZED: Single query to get all message counts using aggregation
            message_counts = Message.objects.filter(
                Q(recipient=user) | Q(sender=user)
            ).aggregate(
                unread_count=Count('id', filter=Q(recipient=user, status='unread')),
                read_count=Count('id', filter=Q(recipient=user, status='read')), 
                sent_count=Count('id', filter=Q(sender=user)),
                archived_count=Count('id', filter=Q(recipient=user, status='archived'))
            )
            
            return {
                'success': True,
                'inbox_messages': inbox_messages,
                'unread_count': message_counts['unread_count'] or 0,
                'read_count': message_counts['read_count'] or 0,
                'sent_count': message_counts['sent_count'] or 0,
                'archived_count': message_counts['archived_count'] or 0
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
            logger.error(f"Error in get_email_dashboard: {str(e)}")
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
        OPTIMIZED: Paginated inbox with efficient joins
        
        Args:
            patient_id: ID of the patient
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            dict: Dictionary containing paginated inbox messages
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Paginated query with sender info loaded
            all_messages = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).select_related(
                'sender'  # Load sender info in same query
            ).order_by('-created_at')
            
            paginator = Paginator(all_messages, page_size)
            try:
                paginated_messages = paginator.get_page(page)
            except:
                paginated_messages = paginator.get_page(1)
            
            return {
                'success': True,
                'messages': paginated_messages,
                'total_count': paginator.count,
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages
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
            logger.error(f"Error in get_inbox_messages: {str(e)}")
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
        OPTIMIZED: Get sent messages with pagination
        
        Args:
            patient_id: ID of the patient
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            dict: Dictionary containing paginated sent messages
        """
        try:
            patient = Patient.objects.select_related('user').get(id=patient_id)
            user = patient.user
            
            # OPTIMIZED: Get sent messages with recipient info loaded
            all_messages = Message.objects.filter(
                sender=user
            ).select_related(
                'recipient'  # Load recipient info in same query
            ).order_by('-created_at')
            
            paginator = Paginator(all_messages, page_size)
            try:
                paginated_messages = paginator.get_page(page)
            except:
                paginated_messages = paginator.get_page(1)
            
            return {
                'success': True,
                'messages': paginated_messages,
                'total_count': paginator.count,
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages
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
            logger.error(f"Error in get_sent_messages: {str(e)}")
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
        OPTIMIZED: Compose and send a new email
        
        Args:
            patient_id: ID of the patient
            recipient_data: Recipient information
            email_data: Email content and subject
            user: User object for sender verification
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.select_related('user', 'primary_provider__user').get(id=patient_id)
            
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
            logger.error(f"Error in compose_email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
