# Create a new file: provider/api/permissions.py

from rest_framework import permissions

class IsProvider(permissions.BasePermission):
    """
    Allows access only to providers.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'provider_profile')

class IsProviderOwner(permissions.BasePermission):
    """
    Object-level permission to only allow providers to access their own data.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if the user is a provider
        if not hasattr(request.user, 'provider_profile'):
            return False
        
        # Check if the object has a provider/doctor field
        if hasattr(obj, 'provider'):
            return obj.provider == request.user.provider_profile
        
        if hasattr(obj, 'doctor'):
            return obj.doctor == request.user.provider_profile
        
        # Check if the object has a user field (for Provider model)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False
