# provider/utils.py

def get_current_provider(request):
    """
    Helper function to consistently get the current provider across all views.
    
    During development and transition, this provides a consistent provider ID
    until proper authentication is implemented.
    """
    # For development: Use a fixed provider ID for consistency
    DEFAULT_PROVIDER_ID = 1
    
    # When authentication is implemented, uncomment the following:
    # if hasattr(request, 'user') and request.user.is_authenticated:
    #     try:
    #         from provider.models import Provider
    #         return Provider.objects.get(user=request.user)
    #     except Provider.DoesNotExist:
    #         pass
    
    # First try getting from session for consistency within a session
    provider_id = request.session.get('current_provider_id', DEFAULT_PROVIDER_ID)
    
    # Store in session for future requests
    request.session['current_provider_id'] = provider_id
    
    # Get provider data consistently - try both approaches
    try:
        # Try direct ORM approach first
        from provider.models import Provider
        provider_obj = Provider.objects.get(id=provider_id)
        
        # Convert to dictionary format for compatibility with repository pattern
        # during transition period
        provider_dict = {
            'id': provider_obj.id,
            'first_name': provider_obj.user.first_name,
            'last_name': provider_obj.user.last_name,
            'specialty': provider_obj.specialty,
            # Add other fields as needed
        }
        
        return provider_dict
    except Exception as e:
        # Fallback to repository approach
        from theme_name.repositories import ProviderRepository
        return ProviderRepository.get_by_id(provider_id)
