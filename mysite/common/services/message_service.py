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

