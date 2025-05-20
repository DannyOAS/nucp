# provider/api/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class VersionedPagination(PageNumberPagination):
    """
    Custom pagination class that adds API version information to paginated responses.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Add API version information to the paginated response.
        """
        # Create the basic paginated response
        response_data = {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        
        # Add version info from the request object if available
        if hasattr(self.request, 'version'):
            response_data['api_version'] = self.request.version
            
        return Response(response_data)
