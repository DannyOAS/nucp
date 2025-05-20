# provider/services/message_service.py
import logging
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json

from django.contrib.auth.models import User
from provider.models import Provider
from patient.models import Patient
from common.models import Message

logger = logging.getLogger(__name__)

class MessageService:
    """Service layer for message-related operations."""
    
    @staticmethod
    def get_provider_emails(provider_id, user_id, folder='inbox', search_query=''):
        """
        Get provider emails based on folder and search:
        - Messages
        - Count statistics
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            user = User.objects.get(id=user_id)
            
            # Get base queryset based on folder
            if folder == 'inbox':
                messages_queryset = Message.objects.filter(
                    recipient=user
                ).exclude(
                    status='deleted'
                )
            elif folder == 'sent':
                messages_queryset = Message.objects.filter(
                    sender=user
                )
            elif folder == 'archived':
                messages_queryset = Message.objects.filter(
                    recipient=user,
                    status='archived'
                )
            elif folder == 'priority':
                messages_queryset = Message.objects.filter(
                    recipient=user,
                    priority='high'
                ).exclude(
                    status='deleted'
                )
            else:
                # Default to inbox
                messages_queryset = Message.objects.filter(
                    recipient=user
                ).exclude(
                    status='deleted'
                )
            
            # Apply search if provided
            if search_query:
                messages_queryset = messages_queryset.filter(
                    Q(subject__icontains=search_query) |
                    Q(content__icontains=search_query) |
                    Q(sender__first_name__icontains=search_query) |
                    Q(sender__last_name__icontains=search_query)
                )
            
            # Apply ordering
            messages_queryset = messages_queryset.order_by('-created_at')
            
            # Get counts for inbox stats
            unread_count = Message.objects.filter(recipient=user, status='unread').count()
            read_count = Message.objects.filter(recipient=user, status='read').count()
            sent_count = Message.objects.filter(sender=user).count()
            archived_count = Message.objects.filter(recipient=user, status='archived').count()
            priority_count = Message.objects.filter(recipient=user, priority='high').exclude(status='deleted').count()
            
            return {
                'messages': messages_queryset,
                'unread_count': unread_count,
                'read_count': read_count,
                'sent_count': sent_count,
                'archived_count': archived_count,
                'priority_count': priority_count
            }
            
        except (Provider.DoesNotExist, User.DoesNotExist):
            logger.error(f"Provider with ID {provider_id} or User with ID {user_id} not found")
            return {
                'messages': [],
                'unread_count': 0,
                'read_count': 0,
                'sent_count': 0,
                'archived_count': 0,
                'priority_count': 0
            }
        except Exception as e:
            logger.error(f"Error in get_provider_emails: {str(e)}")
            raise
    
    @staticmethod
    def get_provider_patients(provider_id):
        """
        Get patients for provider for composing messages
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Get patients assigned to this provider
            patients = Patient.objects.filter(primary_provider=provider)
            
            return patients
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error in get_provider_patients: {str(e)}")
            return []
    
    @staticmethod
    def send_provider_message(message_data, provider_id, user):
        """
        Send a new message from provider
        """
        try:
            provider = Provider.objects.get(id=provider_id)
            
            # Validate required fields
            if not message_data.get('recipient_type'):
                return {
                    'success': False,
                    'error': 'Recipient type is required'
                }
            
            if not message_data.get('recipient_id'):
                return {
                    'success': False,
                    'error': 'Recipient is required'
                }
            
            if not message_data.get('subject'):
                return {
                    'success': False,
                    'error': 'Subject is required'
                }
            
            if not message_data.get('content'):
                return {
                    'success': False,
                    'error': 'Message content is required'
                }
            
            # Get recipient based on type and ID
            recipient_type = message_data.get('recipient_type')
            recipient_id = message_data.get('recipient_id')
            
            try:
                if recipient_type == 'patient':
                    # Recipient is a patient
                    patient = Patient.objects.get(id=recipient_id)
                    recipient = patient.user
                else:
                    # Recipient is a direct user (staff, etc.)
                    recipient = User.objects.get(id=recipient_id)
            except (Patient.DoesNotExist, User.DoesNotExist):
                return {
                    'success': False,
                    'error': 'Recipient not found'
                }
            
            # Create the message
            message = Message.objects.create(
                sender=user,
                sender_type='provider',
                recipient=recipient,
                recipient_type=recipient_type,
                subject=message_data.get('subject'),
                content=message_data.get('content'),
                priority=message_data.get('priority', 'normal'),
                status='unread',
                thread_id=message_data.get('thread_id')
            )
            
            # Handle attachments if provided
            attachments_success = True
            attachments_error = None
            
            if message_data.get('attachments'):
                try:
                    from common.models import MessageAttachment
                    
                    for attachment in message_data.get('attachments'):
                        MessageAttachment.objects.create(
                            message=message,
                            file=attachment,
                            file_name=attachment.name,
                            file_size=attachment.size
                        )
                except Exception as e:
                    attachments_success = False
                    attachments_error = str(e)
                    logger.error(f"Error saving message attachments: {str(e)}")
            
            # Send notification if this is a patient message
            notification_success = True
            notification_error = None
            
            if recipient_type == 'patient':
                try:
                    from common.services.notification_service import NotificationService
                    
                    notification_result = NotificationService.send_message_notification(
                        message=message,
                        notification_type='new_message'
                    )
                    
                    notification_success = notification_result.get('success', False)
                    notification_error = notification_result.get('error')
                except (ImportError, AttributeError):
                    notification_success = False
                    notification_error = 'Notification service not available'
            
            return {
                'success': True,
                'message_id': message.id,
                'attachments': {
                    'success': attachments_success,
                    'error': attachments_error
                },
                'notification': {
                    'success': notification_success,
                    'error': notification_error
                }
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'success': False,
                'error': 'Provider not found'
            }
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_compose_data(provider_id, reply_to_id=None):
        """
        Get data needed for compose form:
        - Patients list
        - Staff members list
        - Original message for replies
        """
        try:
# provider/services/message_service.py (continued)
            provider = Provider.objects.get(id=provider_id)
            
            # Get patients for this provider
            patients = Patient.objects.filter(primary_provider=provider)
            
            # Get staff members (other providers, admins, etc.)
            staff_members = []
            try:
                from django.contrib.auth.models import Group
                staff_group = Group.objects.get(name='Staff')
                staff_users = staff_group.user_set.all()
                
                for user in staff_users:
                    staff_members.append({
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email
                    })
            except (Group.DoesNotExist, AttributeError):
                # If staff group doesn't exist, get other providers
                from provider.models import Provider
                other_providers = Provider.objects.exclude(id=provider_id)
                
                for other_provider in other_providers:
                    if hasattr(other_provider, 'user') and other_provider.user:
                        staff_members.append({
                            'id': other_provider.user.id,
                            'first_name': other_provider.user.first_name,
                            'last_name': other_provider.user.last_name,
                            'email': other_provider.user.email
                        })
            
            # Get original message for reply
            original_message = None
            form_initial = {}
            
            if reply_to_id:
                try:
                    original_message = Message.objects.get(id=reply_to_id)
                    
                    # Pre-fill form with reply data
                    subject = original_message.subject
                    if not subject.startswith('Re:'):
                        subject = f"Re: {subject}"
                    
                    form_initial = {
                        'subject': subject,
                        'recipient_type': original_message.sender_type,
                        'recipient_id': original_message.sender.id,
                        'thread_id': original_message.thread_id or original_message.id
                    }
                except Message.DoesNotExist:
                    original_message = None
            
            return {
                'patients': patients,
                'staff_members': staff_members,
                'original_message': original_message,
                'form_initial': form_initial
            }
            
        except Provider.DoesNotExist:
            logger.error(f"Provider with ID {provider_id} not found")
            return {
                'patients': [],
                'staff_members': [],
                'original_message': None,
                'form_initial': {}
            }
        except Exception as e:
            logger.error(f"Error in get_compose_data: {str(e)}")
            return {
                'patients': [],
                'staff_members': [],
                'original_message': None,
                'form_initial': {}
            }
    
    @staticmethod
    def perform_message_action(message_id, action, user):
        """
        Perform message actions like mark_read, archive, delete
        """
        try:
            message = Message.objects.get(id=message_id)
            
            # Verify user is either sender or recipient
            if message.sender != user and message.recipient != user:
                return {
                    'success': False,
                    'error': 'Permission denied. You are not authorized to perform this action.'
                }
            
            # Perform action based on action type
            if action == 'mark_read':
                if message.status == 'unread':
                    message.status = 'read'
                    message.read_at = timezone.now()
                    message.save()
            elif action == 'mark_unread':
                if message.status == 'read':
                    message.status = 'unread'
                    message.read_at = None
                    message.save()
            elif action == 'archive':
                if message.status != 'deleted':
                    message.status = 'archived'
                    message.save()
            elif action == 'delete':
                message.status = 'deleted'
                message.save()
            elif action == 'restore':
                if message.status in ['archived', 'deleted']:
                    message.status = 'read'
                    message.save()
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
            
            return {
                'success': True,
                'message_id': message.id,
                'new_status': message.status
            }
            
        except Message.DoesNotExist:
            logger.error(f"Message with ID {message_id} not found")
            return {
                'success': False,
                'error': 'Message not found'
            }
        except Exception as e:
            logger.error(f"Error performing message action: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_message_details(message_id, user):
        """
        Get detailed info for a single message:
        - Message details
        - Sender info
        - Thread messages
        """
        try:
            message = Message.objects.get(id=message_id)
            
            # Verify user is either sender or recipient
            if message.sender != user and message.recipient != user:
                return {
                    'success': False,
                    'error': 'Permission denied. You are not authorized to view this message.'
                }
            
            # Mark as read if user is recipient and message is unread
            if message.recipient == user and message.status == 'unread':
                message.status = 'read'
                message.read_at = timezone.now()
                message.save()
            
            # Get thread messages if this is part of a thread
            thread_messages = []
            if message.thread_id:
                thread_messages = Message.objects.filter(
                    thread_id=message.thread_id
                ).exclude(
                    id=message.id  # Exclude the current message
                ).order_by('created_at')
            
            # Get sender info
            sender_info = {
                'id': message.sender.id,
                'name': f"{message.sender.first_name} {message.sender.last_name}",
                'email': message.sender.email,
                'type': message.sender_type
            }
            
            # If sender is a patient or provider, get additional info
            if message.sender_type == 'patient':
                try:
                    patient = Patient.objects.get(user=message.sender)
                    sender_info.update({
                        'ohip_number': patient.ohip_number,
                        'date_of_birth': patient.date_of_birth,
                        'primary_phone': patient.primary_phone
                    })
                except Patient.DoesNotExist:
                    pass
            elif message.sender_type == 'provider':
                try:
                    provider = Provider.objects.get(user=message.sender)
                    sender_info.update({
                        'specialty': provider.specialty,
                        'license_number': provider.license_number
                    })
                except Provider.DoesNotExist:
                    pass
            
            # Get attachments if any
            attachments = []
            try:
                from common.models import MessageAttachment
                attachment_objs = MessageAttachment.objects.filter(message=message)
                
                for attachment in attachment_objs:
                    attachments.append({
                        'id': attachment.id,
                        'file_name': attachment.file_name,
                        'file_size': attachment.file_size,
                        'file_url': attachment.file.url if attachment.file else None,
                        'uploaded_at': attachment.uploaded_at
                    })
            except (ImportError, AttributeError):
                pass
            
            return {
                'success': True,
                'message': message,
                'sender_info': sender_info,
                'thread_messages': thread_messages,
                'attachments': attachments
            }
            
        except Message.DoesNotExist:
            logger.error(f"Message with ID {message_id} not found")
            return {
                'success': False,
                'error': 'Message not found'
            }
        except Exception as e:
            logger.error(f"Error getting message details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_message_templates(template_type):
        """
        Get predefined message templates
        """
        # Define common templates
        templates = {
            'lab_results': {
                'subject': 'Your Recent Lab Results',
                'content': """Dear [Patient Name],

I've reviewed your recent lab results from [Date]. [Result Summary]

[Additional Comments]

Please let me know if you have any questions or concerns.

Regards,
Dr. [Your Name]"""
            },
            'prescription_renewal': {
                'subject': 'Prescription Renewal',
                'content': """Dear [Patient Name],

Your prescription for [Medication] has been renewed for [Duration/Quantity].

[Instructions]

Please contact our office if you have any questions.

Regards,
Dr. [Your Name]"""
            },
            'appointment_confirmation': {
                'subject': 'Appointment Confirmation',
                'content': """Dear [Patient Name],

This is to confirm your appointment scheduled for [Date] at [Time].

[Additional Instructions]

If you need to reschedule, please contact our office at least 24 hours in advance.

Regards,
Dr. [Your Name]"""
            },
            'post_visit': {
                'subject': 'Visit Summary',
                'content': """Dear [Patient Name],

Thank you for your visit today. As discussed during your appointment:

[Visit Summary]

[Follow-up Instructions]

Please don't hesitate to contact us if you have any questions.

Regards,
Dr. [Your Name]"""
            },
            'referral': {
                'subject': 'Referral Information',
                'content': """Dear [Patient Name],

I've referred you to [Specialist Name] for [Reason].

The referral has been sent, and their office should contact you within [Timeframe] to schedule an appointment.

[Additional Information]

Regards,
Dr. [Your Name]"""
            },
            'test_preparation': {
                'subject': 'Test Preparation Instructions',
                'content': """Dear [Patient Name],

You are scheduled for [Test Name] on [Date] at [Time].

Please follow these preparation instructions:

[Instructions]

If you have any questions about these preparations, please contact our office.

Regards,
Dr. [Your Name]"""
            }
        }
        
        # Check if requested template exists
        if template_type in templates:
            return templates[template_type]
        
        # If not found, or template_type is empty, return empty template
        return {
            'subject': '',
            'content': ''
        }
