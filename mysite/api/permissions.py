# api/permissions.py
from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Base permission for object-level permissions based on ownership.
    Subclasses should override the has_object_permission method.
    
    This acts as a base class for both IsPatientOwner and IsProviderOwner.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Default implementation, subclasses should override this
        return False

class IsPatient(permissions.BasePermission):
    """
    Permission to only allow patients to access a view.
    
    This checks if the current user has a patient_profile attribute,
    which indicates they are a registered patient.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'patient_profile')

class IsProvider(permissions.BasePermission):
    """
    Permission to only allow providers to access a view.
    
    This checks if the current user has a provider_profile attribute,
    which indicates they are a registered healthcare provider.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'provider_profile')

class IsPatientOwner(IsOwner):
    """
    Object-level permission to only allow patients to access their own data.
    
    This extends the base IsOwner permission and checks if:
    1. The user has a patient profile
    2. The object belongs to that patient (via patient or user field)
    """
    def has_object_permission(self, request, view, obj):
        # First check the base class permissions (read methods)
        if super().has_object_permission(request, view, obj):
            return True
        
        # Check if the user is a patient
        if not hasattr(request.user, 'patient_profile'):
            return False
        
        # Check if the object has a patient field
        if hasattr(obj, 'patient'):
            if isinstance(obj.patient, type(request.user.patient_profile)):
                return obj.patient == request.user.patient_profile
            else:
                return obj.patient == request.user
        
        # Check if the object has a user field (for Patient model)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

class IsProviderOwner(IsOwner):
    """
    Object-level permission to only allow providers to access their own data.
    
    This extends the base IsOwner permission and checks if:
    1. The user has a provider profile
    2. The object belongs to that provider (via provider, doctor, or user field)
    """
    def has_object_permission(self, request, view, obj):
        # First check the base class permissions (read methods)
        if super().has_object_permission(request, view, obj):
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

class IsMessageParticipant(permissions.BasePermission):
    """
    Permission to only allow message participants (sender or recipient) to access a message.
    
    This ensures that only users who sent or received a message can view it.
    """
    def has_object_permission(self, request, view, obj):
        # Message objects have sender and recipient fields
        if hasattr(obj, 'sender') and hasattr(obj, 'recipient'):
            return obj.sender == request.user or obj.recipient == request.user
        
        return False

class IsPatientOrProvider(permissions.BasePermission):
    """
    Permission to allow either patients or providers to access a view.
    
    This can be used for resources accessible to both user types.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        return (hasattr(request.user, 'patient_profile') or 
                hasattr(request.user, 'provider_profile'))

class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users to access a view.
    
    This checks if the user has the is_staff flag set to True.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
