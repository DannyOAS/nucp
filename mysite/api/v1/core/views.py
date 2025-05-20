# api/v1/core/views.py
from api.views import BaseUserViewSet as OriginalUserViewSet
from api.views import BaseGroupViewSet as OriginalGroupViewSet

class UserViewSet(OriginalUserViewSet):
    """
    API v1 endpoint for users.
    Extends the original UserViewSet for proper versioning.
    """
    pass

class GroupViewSet(OriginalGroupViewSet):
    """
    API v1 endpoint for groups.
    Extends the original GroupViewSet for proper versioning.
    """
    pass
