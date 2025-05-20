# Update mysite/api/v1/core/views.py
from api.views import BaseUserViewSet as OriginalUserViewSet
from api.views import BaseGroupViewSet as OriginalGroupViewSet
from api.versioning import VersionedViewMixin

class UserViewSet(VersionedViewMixin, OriginalUserViewSet):
    """
    API v1 endpoint for users.
    Extends the original UserViewSet for proper versioning.
    """
    version = 'v1'

class GroupViewSet(VersionedViewMixin, OriginalGroupViewSet):
    """
    API v1 endpoint for groups.
    Extends the original GroupViewSet for proper versioning.
    """
    version = 'v1'
