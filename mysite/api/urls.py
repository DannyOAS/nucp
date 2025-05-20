# mysite/api/urls.py
from django.urls import path, include, re_path
from django.http import HttpResponseRedirect
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authtoken import views as token_views
from . import views

app_name = 'api'

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

# Legacy redirect function - improved implementation
def legacy_redirect(request, path=''):
    """Redirect legacy API paths to versioned ones"""
    return HttpResponseRedirect(f'/api/v1/{path}')

urlpatterns = [
    # API documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Version 1 API
    path('v1/', include('api.v1.urls')),
    
    # Legacy API redirects - these need to be BEFORE the api/ include
    # We use r'^provider/' instead of r'^provider' to ensure the pattern matches correctly
    re_path(r'^provider/(?P<path>.*)', lambda request, path: HttpResponseRedirect(f'/api/v1/provider/{path}')),
    re_path(r'^patient/(?P<path>.*)', lambda request, path: HttpResponseRedirect(f'/api/v1/patient/{path}')),
    
    # Root path redirect
    path('', lambda request: HttpResponseRedirect('v1/')),
]
