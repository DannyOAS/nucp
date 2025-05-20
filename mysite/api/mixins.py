# mysite/api/mixins.py
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

class PaginationMixin:
    """Mixin providing standardized pagination functionality for viewsets"""
    
    def paginate_queryset_with_context(self, queryset):
        """Apply pagination and return a standardized response"""
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class MessageActionsMixin:
    """Mixin providing standard message-related actions for viewsets"""
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get received messages"""
        queryset = self.get_message_model().objects.filter(
            recipient=request.user
        ).exclude(
            status='deleted'
        ).order_by('-created_at')
        
        return self.paginate_queryset_with_context(queryset)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get sent messages"""
        queryset = self.get_message_model().objects.filter(
            sender=request.user
        ).order_by('-created_at')
        
        return self.paginate_queryset_with_context(queryset)
    
    def get_message_model(self):
        """Override this method in the implementing viewset to return the Message model"""
        from common.models import Message
        return Message

class FilterMixin:
    """Mixin providing standardized filtering functionality"""
    
    def apply_filters(self, queryset):
        """Apply filters from query parameters based on filter_fields mapping"""
        if not hasattr(self, 'filter_fields'):
            return queryset
            
        for param, field in self.filter_fields.items():
            value = self.request.query_params.get(param)
            if value:
                filter_kwargs = {field: value}
                queryset = queryset.filter(**filter_kwargs)
        
        return queryset
    
    def get_queryset(self):
        """
        Override the default get_queryset to apply filters
        Implementing classes should call super().get_queryset()
        """
        queryset = super().get_queryset()
        return self.apply_filters(queryset)

class SearchMixin:
    """Mixin providing standardized search functionality"""
    
    def apply_search(self, queryset):
        """Apply text search across specified fields"""
        if not hasattr(self, 'search_fields'):
            return queryset
            
        search_term = self.request.query_params.get('search')
        if search_term:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_term})
            
            queryset = queryset.filter(q_objects)
        
        return queryset
    
    def get_queryset(self):
        """
        Override the default get_queryset to apply search
        Implementing classes should call super().get_queryset()
        """
        queryset = super().get_queryset()
        return self.apply_search(queryset)
