"""
Provider utility functions.
This module contains utility functions for working with Provider objects,
including retrieving the current provider based on the authenticated user.
"""

import logging
from django.shortcuts import redirect
from django.contrib import messages
from provider.models import Provider

logger = logging.getLogger(__name__)

def get_current_provider(request, redirect_on_failure=True):
    """
    Get the Provider object for the currently authenticated user.
    
    This is the central function for retrieving the current provider.
    All provider views should use this function to ensure consistency.
    
    Args:
        request: The HTTP request object containing the authenticated user
        redirect_on_failure: Whether to redirect to unauthorized page if no provider is found
        
    Returns:
        tuple: (provider_obj, provider_dict)
            - provider_obj: The Provider model instance
            - provider_dict: Dictionary representation compatible with templates
            
    Note:
        If no provider is found and redirect_on_failure is True, this function
        will redirect to the 'unauthorized' view and not return.
    """
    user = request.user
    
    # Check if user is authenticated
    if not user.is_authenticated:
        logger.warning("Unauthenticated user attempting to access provider view")
        if redirect_on_failure:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('login')
        return None, None
    
    # Check if user is in providers group
    if not user.groups.filter(name='providers').exists():
        logger.warning(f"User {user.username} is not in providers group")
        if redirect_on_failure:
            return redirect('unauthorized')
        return None, None
    
    try:
        # Get the provider associated with this user
        provider = Provider.objects.get(user=user)
        
        # Create a dictionary representation compatible with templates
        provider_dict = {
            'id': provider.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'specialty': getattr(provider, 'specialty', 'General'),
            'is_active': getattr(provider, 'is_active', True),
        }
        
        logger.info(f"Provider retrieved: ID {provider.id}, User: {user.username}")
        return provider, provider_dict
        
    except Provider.DoesNotExist:
        logger.warning(f"No Provider record found for authenticated user: {user.username}")
        
        # Auto-create a provider record as a fallback during transition
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
                'is_active': provider.is_active,
            }
            
            logger.info(f"Created new Provider record for user: {user.username}")
            return provider, provider_dict
            
        except Exception as e:
            logger.error(f"Failed to create Provider record: {str(e)}")
            if redirect_on_failure:
                messages.error(request, "There was an error setting up your provider account.")
                return redirect('unauthorized')
            return None, None
    
    except Exception as e:
        logger.error(f"Error retrieving provider: {str(e)}")
        if redirect_on_failure:
            messages.error(request, "There was an error retrieving your provider information.")
            return redirect('unauthorized')
        return None, None
