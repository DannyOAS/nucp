# patient/services/message_service.py
from common.models import Message
from django.contrib.auth.models import User, Group
from django.utils import timezone
from patient.models import Patient

class MessageService:
    @staticmethod
    def get_inbox_messages(patient):
        """Get inbox messages for a patient"""
        return Message.objects.filter(
            recipient=patient.user
        ).exclude(
            status='deleted'
        ).order_by('-created_at')
    
    @staticmethod
    def get_sent_messages(patient):
        """Get sent messages for a patient"""
        return Message.objects.filter(
            sender=patient.user
        ).order_by('-created_at')
    
    @staticmethod
    def get_archived_messages(patient):
        """Get archived messages for a patient"""
        return Message.objects.filter(
            recipient=patient.user,
            status='archived'
        ).order_by('-created_at')
    
    @staticmethod
    def get_message_by_id(message_id):
        """Get a message by ID"""
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return None
    
    @staticmethod
    def send_message(sender, subject, content, recipient=None, recipient_type=None):
        """
        Send a new message
        
        Args:
            sender: User model instance (sender)
            subject: Message subject
            content: Message content
            recipient: User model instance (recipient) - optional
            recipient_type: Type of recipient (e.g., 'provider', 'pharmacy') - optional
            
        Returns:
            Message: The created message
            or
            dict: Error details if message couldn't be sent
        """
        try:
            # If recipient is provided directly, use it
            if recipient:
                message = Message.objects.create(
                    sender=sender,
                    recipient=recipient,
                    subject=subject,
                    content=content,
                    status='unread'
                )
                return message
            
            # Otherwise, determine recipient based on type
            if recipient_type == 'provider':
                # Find the patient's primary provider
                try:
                    patient = Patient.objects.get(user=sender)
                    if patient.primary_provider:
                        provider_user = patient.primary_provider.user
                        message = Message.objects.create(
                            sender=sender,
                            recipient=provider_user,
                            subject=subject,
                            content=content,
                            status='unread'
                        )
                        return message
                    return {'error': 'No primary provider assigned to this patient'}
                except Patient.DoesNotExist:
                    return {'error': 'Patient profile not found'}
                    
            elif recipient_type == 'pharmacy':
                # Find pharmacy staff
                pharmacy_group = Group.objects.filter(name='pharmacy').first()
                if pharmacy_group:
                    # Get the first pharmacy staff member (simplified)
                    pharmacy_user = pharmacy_group.user_set.first()
                    if pharmacy_user:
                        message = Message.objects.create(
                            sender=sender,
                            recipient=pharmacy_user,
                            subject=subject,
                            content=content,
                            status='unread'
                        )
                        return message
                return {'error': 'No pharmacy staff found'}
                
            elif recipient_type == 'billing':
                # Find billing staff
                billing_group = Group.objects.filter(name='billing').first()
                if billing_group:
                    # Get the first billing staff member (simplified)
                    billing_user = billing_group.user_set.first()
                    if billing_user:
                        message = Message.objects.create(
                            sender=sender,
                            recipient=billing_user,
                            subject=subject,
                            content=content,
                            status='unread'
                        )
                        return message
                return {'error': 'No billing staff found'}
                
            return {'error': 'Invalid recipient type'}
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def update_message_status(message_id, new_status, user):
        """
        Update a message's status (read, unread, archived, deleted)
        
        Args:
            message_id: ID of the message to update
            new_status: New status value
            user: User performing the action
            
        Returns:
            dict: Success or error information
        """
        try:
            # Get the message and verify ownership
            message = Message.objects.get(id=message_id)
            
            # Verify user is either the sender or recipient
            if message.sender != user and message.recipient != user:
                return {'success': False, 'error': 'Not authorized to modify this message'}
            
            # Check status validity
            valid_statuses = ['read', 'unread', 'archived', 'deleted']
            if new_status not in valid_statuses:
                return {'success': False, 'error': 'Invalid status value'}
            
            # Update status
            message.status = new_status
            message.save()
            
            return {'success': True, 'message': message}
            
        except Message.DoesNotExist:
            return {'success': False, 'error': 'Message not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
