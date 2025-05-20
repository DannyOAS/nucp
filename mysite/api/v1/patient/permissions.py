# patient/api/permissions.py
from django.contrib.auth.models import User
from rest_framework import permissions

class IsPatientOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow patients to access their own data.
    """
#    def has_object_permission(self, request, view, obj):
#        # Read permissions are allowed to any request
#        if request.method in permissions.SAFE_METHODS:
#            return True
#        
#        # Write permissions are only allowed to the owner
#        if hasattr(request.user, 'patient_profile'):
#            # Check if the object has a patient field
#            if hasattr(obj, 'patient'):
#                return obj.patient == request.user.patient_profile
#            
#            # For messages, check both sender and recipient
#            if hasattr(obj, 'sender') and hasattr(obj, 'recipient'):
#                return (obj.sender == request.user or 
#                        obj.recipient == request.user)
#                
#        return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        if hasattr(request.user, 'patient_profile'):
            # Check if the object has a patient field
            if hasattr(obj, 'patient'):
                # If patient is a User model, compare directly with request.user
                if isinstance(obj.patient, User):
                    return obj.patient == request.user
                # If patient is a Patient model, compare with patient_profile
                else:
                    return obj.patient == request.user.patient_profile
            
            # For messages, check both sender and recipient
            if hasattr(obj, 'sender') and hasattr(obj, 'recipient'):
                return (obj.sender == request.user or 
                        obj.recipient == request.user)
                
        return False

class IsPatientOwner(permissions.BasePermission):
    """
    Permission to only allow patients to access their own data.
    More restrictive than IsPatientOrReadOnly.
    """
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'patient_profile'):
            return False
            
        # Check if the object has a patient field
        if hasattr(obj, 'patient'):
            return obj.patient == request.user.patient_profile
            
        # For direct patient data
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False
