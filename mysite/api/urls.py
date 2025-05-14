# api/urls.py
from django.urls import path, include
from django.http import HttpResponseRedirect
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authtoken import views as token_views  # Add this import
from . import views

app_name = 'api'  # Add this line

# Create schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Healthcare API",
        default_version='v1',
        description="API for Northern Health Innovations platform",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="admin@example.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)

# Create a router for base API views
router = DefaultRouter()
router.register(r'users', views.BaseUserViewSet, basename='user')
router.register(r'groups', views.BaseGroupViewSet, basename='group')

urlpatterns = [
    # API documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Version 1 API
    path('v1/', include([
        path('', include(router.urls)),
        path('auth/', include('rest_framework.urls')),
        path('token-auth/', token_views.obtain_auth_token, name='api-token-auth'),
    ])),
    
    # Redirect root to v1
    path('', lambda request: HttpResponseRedirect('v1/')),
]
