# mysite/api/versioning.py
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

class VersionedPagination(PageNumberPagination):
    """Pagination class that adds API version to all paginated responses"""
    
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        if hasattr(self.request, 'version'):
            response.data['api_version'] = self.request.version
        return response

class VersionedViewMixin:
    """Mixin for views to include API version in all responses"""
    pagination_class = VersionedPagination
    
    def get_success_headers(self, data):
        """Add version to headers for created objects"""
        headers = super().get_success_headers(data)
        if hasattr(self.request, 'version'):
            headers['X-API-Version'] = self.request.version
        return headers
    
    def finalize_response(self, request, response, *args, **kwargs):
        """Add version to all responses"""
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Only add to successful responses with data
        if 200 <= response.status_code < 300 and hasattr(response, 'data'):
            if isinstance(response.data, dict) and 'api_version' not in response.data:
                if hasattr(request, 'version'):
                    response.data['api_version'] = request.version
                else:
                    # Default version if not specified in request
                    response.data['api_version'] = getattr(self, 'version', 'v1')
        
        return response
