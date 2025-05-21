# patient/services/message_service.py
from common.models import Message
from patient.models import Patient
from django.utils import timezone

class MessageService:
    """Service layer for patient message operations"""
    
    @staticmethod
    def get_patient_messages(patient_id):
        """
        Get inbox messages for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Dictionary containing messages data
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get messages for this user
            messages_list = Message.objects.filter(
                recipient=user
            ).exclude(
                status='deleted'
            ).order_by('-created_at')
            
            # Get unread count
            unread_count = Message.objects.filter(
                recipient=user,
                status='unread'
            ).count()
            
            return {
                'success': True,
                'messages': messages_list,
                'unread_count': unread_count
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'messages': [],
                'unread_count': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'messages': [],
                'unread_count': 0
            }
    
    @staticmethod
    def get_message_details(message_id, patient_id):
        """
        Get details for a specific message
        
        Args:
            message_id: ID of the message
            patient_id: ID of the patient (for ownership verification)
            
        Returns:
            dict: Result containing message data if successful
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            user = patient.user
            
            # Get message and verify ownership
            message = Message.objects.get(id=message_id, recipient=user)
            
            # Mark as read if unread
            if message.status == 'unread':
                message.status = 'read'
                message.read_at = timezone.now()
                message.save()
            
            return {
                'success': True,
                'message': message
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Message.DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found or not authorized'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_compose_form_data(patient_id):
        """
        Get data for message compose form
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            dict: Form data including recipient choices
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Define recipient choices
            recipient_choices = [
                ('provider', 'My Provider'),
                ('pharmacy', 'Pharmacy'),
                ('billing', 'Billing Department')
            ]
            
            return {
                'success': True,
                'recipient_choices': recipient_choices
            }
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found',
                'recipient_choices': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'recipient_choices': []
            }
    
    @staticmethod
    def send_patient_message(patient_id, message_data, user):
        """
        Send a new message from a patient
        
        Args:
            patient_id: ID of the patient
            message_data: Data for the message
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
                    'error': 'Not authorized to send messages as this patient'
                }
            
            # Extract message data
            subject = message_data.get('subject')
            content = message_data.get('content')
            recipient_type = message_data.get('recipient_type')
            
            # Validate required fields
            if not all([subject, content, recipient_type]):
                return {
                    'success': False,
                    'error': 'Subject, content, and recipient type are required'
                }
            
            # Determine recipient based on type
            recipient = None
            if recipient_type == 'provider' and patient.primary_provider:
                recipient = patient.primary_provider.user
            elif recipient_type == 'pharmacy':
                # You might need to implement pharmacy user lookup
                # For now, using a placeholder approach
                from django.contrib.auth.models import Group
                pharmacy_group = Group.objects.filter(name='pharmacy').first()
                if pharmacy_group and pharmacy_group.user_set.exists():
                    recipient = pharmacy_group.user_set.first()
            elif recipient_type == 'billing':
                # Similar placeholder for billing
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
    
    @staticmethod
    def perform_message_action(message_id, patient_id, action, user):
        """
        Perform an action on a message (mark read/unread, archive, delete)
        
        Args:
            message_id: ID of the message
            patient_id: ID of the patient (for ownership verification)
            action: Action to perform (mark_read, mark_unread, archive, delete)
            user: User object for verification
            
        Returns:
            dict: Result of the operation
        """
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Verify user ownership
            if patient.user != user:
                return {
                    'success': False,
                    'error': 'Not authorized to modify messages for this patient'
                }
            
            # Get message and verify ownership
            message = Message.objects.get(id=message_id)
            
            # Verify user is either the sender or recipient
            if message.sender != user and message.recipient != user:
                return {
                    'success': False, 
                    'error': 'Not authorized to modify this message'
                }
            
            # Perform the requested action
            if action == 'mark_read':
                message.status = 'read'
                message.read_at = timezone.now()
                message.save()
            elif action == 'mark_unread':
                message.status = 'unread'
                message.read_at = None
                message.save()
            elif action == 'archive':
                message.status = 'archived'
                message.save()
            elif action == 'delete':
                message.status = 'deleted'
                message.save()
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
            
            return {
                'success': True,
                'message': message
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'error': 'Patient not found'
            }
        except Message.DoesNotExist:
            return {
                'success': False,
                'error': 'Message not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
