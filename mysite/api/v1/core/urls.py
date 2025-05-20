# api/v1/core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.v1.core.views import UserViewSet, GroupViewSet

# Create a router for core v1 endpoints
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
]
