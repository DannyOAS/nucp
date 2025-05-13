# provider/utils.py
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

def get_current_provider(request):
    """
    Utility function to get the current provider from the authenticated user.
    Returns a tuple of (provider, provider_dict) where:
    - provider is the Provider model instance
    - provider_dict is a dictionary with provider data for templates
    
    If the user is not a provider, redirects to unauthorized and returns (None, None).
    """
    user = request.user
    
    # Check that user is authenticated
    if not user.is_authenticated:
        return None, None
    
    # Check if user is in providers group
    is_provider = user.groups.filter(name='providers').exists() or user.is_staff
    
    if not is_provider:
        return None, None
    
    # Get provider associated with this user
    from provider.models import Provider
    try:
        provider = Provider.objects.get(user=user)
        # Create a dictionary compatible with existing templates
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': getattr(provider, 'specialty', 'General'),
            'is_active': getattr(provider, 'is_active', True),
        }
        return provider, provider_dict
    except Provider.DoesNotExist:
        # Create a provider record if it doesn't exist
        try:
            provider = Provider.objects.create(
                user=user,
                license_number=f'TMP{user.id}',
                specialty='General',
                is_active=True
            )
            provider_dict = {
                'id': provider.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'specialty': provider.specialty,
            }
            return provider, provider_dict
        except Exception as e:
            logger.error(f"Error creating provider for user {user.id}: {str(e)}")
            return None, None
