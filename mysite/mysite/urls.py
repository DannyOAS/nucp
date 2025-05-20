# mysite/mysite/urls.py
from django.contrib import admin
from django.urls import include, path, re_path
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Simplest approach - direct endpoint mapping
def legacy_provider_redirect(request, endpoint=''):
    """Redirect legacy provider API paths to versioned ones"""
    return HttpResponseRedirect(f'/api/v1/provider/{endpoint}')

def legacy_patient_redirect(request, endpoint=''):
    """Redirect legacy patient API paths to versioned ones"""
    return HttpResponseRedirect(f'/api/v1/patient/{endpoint}')

schema_view = get_schema_view(
    openapi.Info(
        title="Healthcare Portal API",
        default_version='v1',
        description="API documentation for the Healthcare Portal",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("theme_name.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path('login/', lambda request: redirect('https://auth.isnord.ca/'), name='login'),
    
    # Include app URLs
    path('provider/', include('provider.urls')),
    path('patient/', include('patient.urls')),
    
    # Legacy API redirects - using the simpler approach with specific functions
    path('api/provider/', legacy_provider_redirect),
    re_path(r'^api/provider/(?P<endpoint>.+)$', legacy_provider_redirect),
    path('api/patient/', legacy_patient_redirect),
    re_path(r'^api/patient/(?P<endpoint>.+)$', legacy_patient_redirect),
    
    # Versioned API - v1
    path('api/v1/', include('api.v1.urls')),
    
    # Other legacy API endpoints (redirect to versioned)
    path('api/', lambda request: redirect('/api/v1/')),
    path('api/users/', lambda request: redirect('/api/v1/users/')),
    path('api/groups/', lambda request: redirect('/api/v1/groups/')),
    
    # Swagger documentation
    re_path(r'^api/docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Unauthorized page
    path('unauthorized/', 
         lambda request: HttpResponse("Unauthorized access. You don't have permission to access this resource.", status=403), 
         name='unauthorized'),
]
