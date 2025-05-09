from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)

class AutheliaMiddleware:
    """
    Middleware to handle Authelia authentication via HTTP headers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip for certain paths
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
            
        # Check if user is already authenticated
        if request.user.is_authenticated:
            return self.get_response(request)
            
        # Check for Authelia headers
        remote_user = request.META.get('HTTP_REMOTE_USER')
        remote_name = request.META.get('HTTP_REMOTE_NAME')
        remote_email = request.META.get('HTTP_REMOTE_EMAIL')
        remote_groups = request.META.get('HTTP_REMOTE_GROUPS', '')
        
        if remote_user:
            logger.debug(f"Authelia user found: {remote_user}")
            
            # Authenticate using the Authelia header
            user = authenticate(
                request=request,
                username=remote_user,
                email=remote_email,
                remote_name=remote_name,
                remote_groups=remote_groups
            )
            
            if user:
                # Log the user in
                login(request, user)
                logger.info(f"User {user.username} logged in via Authelia")
            else:
                logger.warning(f"Failed to authenticate Authelia user: {remote_user}")
                # Let them continue but they may hit permission errors later
        
        # Let the request continue - Authelia will handle auth redirects at the proxy level
        return self.get_response(request)
