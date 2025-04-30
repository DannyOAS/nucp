import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
from django.conf import settings
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email sending via IredMail server or Django's email backend"""
    
    @staticmethod
    def send_message(sender, recipient, subject, body, priority='normal', attachments=None):
        """
        Send an email message using configured email backend
        
        Args:
            sender (str): Email address of sender
            recipient (str): Email address of recipient
            subject (str): Email subject
            body (str): Email body content (plain text)
            priority (str): Email priority ('high', 'normal', 'low')
            attachments (list): List of file objects to attach
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Check if IredMail is configured and should be used
            if hasattr(settings, 'IREDMAIL_ENABLED') and settings.IREDMAIL_ENABLED:
                return EmailService._send_via_iredmail(
                    sender=sender,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    priority=priority,
                    attachments=attachments
                )
            else:
                # Fall back to Django's email backend
                return EmailService._send_via_django(
                    sender=sender,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    priority=priority,
                    attachments=attachments
                )
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def _send_via_iredmail(sender, recipient, subject, body, priority='normal', attachments=None):
        """
        Send email using direct SMTP connection to IredMail server
        
        This method connects directly to your IredMail server using SMTP
        """
        try:
            # Get IredMail configuration from settings
            smtp_host = settings.IREDMAIL_SMTP_HOST
            smtp_port = settings.IREDMAIL_SMTP_PORT
            smtp_user = settings.IREDMAIL_SMTP_USER
            smtp_pass = settings.IREDMAIL_SMTP_PASSWORD
            use_tls = getattr(settings, 'IREDMAIL_USE_TLS', True)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = subject
            
            # Set priority headers if high priority
            if priority == 'high':
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
                msg['Importance'] = 'High'
            
            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Also create HTML version if body contains HTML markers
            if '<html>' in body or '<body>' in body or '<div>' in body or '<p>' in body:
                msg.attach(MIMEText(body, 'html'))
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    # Read file data
                    file_data = attachment.read()
                    part = MIMEApplication(file_data, Name=attachment.name)
                    
                    # Add header
                    part['Content-Disposition'] = f'attachment; filename="{attachment.name}"'
                    msg.attach(part)
                    
                    # Reset file pointer for potential future use
                    attachment.seek(0)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                
                # Login if credentials provided
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                
                # Send email
                server.send_message(msg)
            
            logger.info(f"Email sent via IredMail: {subject} to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via IredMail: {str(e)}")
            # Try to fall back to Django's email backend
            return EmailService._send_via_django(
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                priority=priority,
                attachments=attachments
            )
    
    @staticmethod
    def _send_via_django(sender, recipient, subject, body, priority='normal', attachments=None):
        """
        Send email using Django's email backend
        """
        try:
            # Determine if we need to send HTML email
            html_content = None
            if '<html>' in body or '<body>' in body or '<div>' in body or '<p>' in body:
                html_content = body
                plain_content = strip_tags(body)
            else:
                plain_content = body
            
            # Create email message
            if html_content:
                # Create message with both HTML and plain text
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_content,
                    from_email=sender,
                    to=[recipient]
                )
                email.attach_alternative(html_content, "text/html")
            else:
                # Plain text only
                email = EmailMessage(
                    subject=subject,
                    body=plain_content,
                    from_email=sender,
                    to=[recipient]
                )
            
            # Set priority headers if high priority
            if priority == 'high':
                email.extra_headers['X-Priority'] = '1'
                email.extra_headers['X-MSMail-Priority'] = 'High'
                email.extra_headers['Importance'] = 'High'
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    email.attach(attachment.name, attachment.read(), attachment.content_type)
                    # Reset file pointer
                    attachment.seek(0)
            
            # Send email
            email.send()
            
            logger.info(f"Email sent via Django: {subject} to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via Django: {str(e)}")
            return False
    
    @staticmethod
    def send_templated_message(sender, recipient, template_name, context, subject, priority='normal', attachments=None):
        """
        Send an email using a template
        
        Args:
            sender (str): Email address of sender
            recipient (str): Email address of recipient
            template_name (str): Name of the email template to use
            context (dict): Context data to render the template with
            subject (str): Email subject
            priority (str): Email priority ('high', 'normal', 'low')
            attachments (list): List of file objects to attach
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Render HTML content from template
            html_content = render_to_string(f'emails/{template_name}.html', context)
            
            # Create plain text version
            plain_content = strip_tags(html_content)
            
            # Send the message
            return EmailService.send_message(
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=html_content,  # Send as HTML
                priority=priority,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Failed to send templated email: {str(e)}")
            return False

    @staticmethod
    def test_connection():
        """
        Test email connection to verify configuration
        
        Returns:
            dict: Status and message indicating success or failure
        """
        try:
            # Check which email method to test
            if hasattr(settings, 'IREDMAIL_ENABLED') and settings.IREDMAIL_ENABLED:
                # Test IredMail connection
                smtp_host = settings.IREDMAIL_SMTP_HOST
                smtp_port = settings.IREDMAIL_SMTP_PORT
                smtp_user = settings.IREDMAIL_SMTP_USER
                smtp_pass = settings.IREDMAIL_SMTP_PASSWORD
                use_tls = getattr(settings, 'IREDMAIL_USE_TLS', True)
                
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    if use_tls:
                        server.starttls()
                    
                    # Login if credentials provided
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                
                return {
                    'status': 'success',
                    'message': f'Successfully connected to IredMail server at {smtp_host}:{smtp_port}'
                }
            else:
                # Test Django email backend
                test_email = EmailMessage(
                    subject='Test Connection',
                    body='This is a test email to verify connection.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.DEFAULT_FROM_EMAIL]  # Send to self
                )
                test_email.send(fail_silently=False)
                
                return {
                    'status': 'success',
                    'message': f'Successfully connected to email backend: {settings.EMAIL_BACKEND}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection test failed: {str(e)}'
            }
