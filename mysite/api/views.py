# api/views.py
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .serializers import (
    UserSerializer, GroupSerializer, BasePatientSerializer,
    BaseProviderSerializer, BaseAppointmentSerializer,
    BasePrescriptionSerializer, BasePrescriptionRequestSerializer,
    BaseMessageSerializer
)
from .permissions import (
    IsPatient, IsProvider, IsPatientOwner, IsProviderOwner,
    IsMessageParticipant, IsAdminUser
)

class BaseUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base API endpoint for user profiles.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change the user's password"""
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(current_password):
            return Response(
                {'detail': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully.'})

class BaseGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base API endpoint for user groups.
    Only accessible by admin users.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

class BaseViewSet(viewsets.ModelViewSet):
    """
    Base viewset with common functionality.
    Provides basic error handling for actions.
    """
    def perform_action_with_error_handling(self, action_func, success_message, error_message):
        """
        Perform an action with standardized error handling
        
        Args:
            action_func: Function to execute
            success_message: Message to return on success
            error_message: Message to return on error
            
        Returns:
            Response: API response with appropriate status
        """
        try:
            result = action_func()
            if isinstance(result, dict) and result.get('error'):
                return Response(
                    {'detail': f"{error_message}: {result.get('error')}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_data = {'detail': success_message}
            if isinstance(result, dict) and result.get('data'):
                response_data.update(result.get('data'))
                
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': f"{error_message}: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
