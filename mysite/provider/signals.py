# provider/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Provider
from common.utils.ldap_client import LDAPClient
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_or_update_provider(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create or update Provider records when User objects are created/updated.
    This ensures every authenticated user has an associated Provider record if they're in the right groups.
    """
    # Check if the user is in the 'Providers' group or has 'is_staff' set
    is_provider = False
    
    if hasattr(instance, 'groups'):
        is_provider = instance.groups.filter(name='Providers').exists()
    
    # If this is a provider user, ensure they have a Provider record
    if is_provider or instance.is_staff:
        # Get or create a Provider for this user
        provider, created = Provider.objects.get_or_create(
            user=instance,
            defaults={
                'license_number': f'TMP{instance.id}',  # Temporary until set properly
                'specialty': 'General',  # Default value
                'is_active': True
            }
        )
        
        # If this is an existing provider, ensure name fields are synced
        if not created:
            # You might want to update certain fields here to keep them in sync
            # This depends on your requirements
            pass

@receiver(post_save, sender=Provider)
def provider_saved(sender, instance, created, **kwargs):
    """
    Signal handler that runs when a Provider is saved.
    This ensures the associated user is added to the providers group in LDAP.
    """
    if not instance.user:
        logger.warning("Provider saved without associated user")
        return
    
    logger.info(f"Provider saved: {instance.id}, User: {instance.user.username}")
    
    # Connect to LDAP
    ldap_client = LDAPClient()
    
    # Check if user exists in LDAP
    if ldap_client.user_exists(instance.user.username):
        # User exists, just add to providers group
        ldap_client.add_user_to_providers(instance.user.username)
    else:
        # User doesn't exist in LDAP, create and add to providers group
        user_data = {
            'username': instance.user.username,
            'first_name': instance.user.first_name,
            'last_name': instance.user.last_name,
            'email': instance.user.email,
            'title': 'MD',  # Default title
            'password_hash': '{SSHA}DummyHash'  # This needs a real hash
        }
        
        ldap_client.create_user(user_data)
        ldap_client.add_user_to_providers(instance.user.username)
    
    # Clean up
    ldap_client.disconnect()
