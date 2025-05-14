"""
URL configuration for mysite project.
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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
    path("", include("theme_name.urls")),  # Include theme URLs without patient/provider URLs
    path("__reload__/", include("django_browser_reload.urls")),
    path('login/', lambda request: redirect('https://auth.isnord.ca/'), name='login'),
    
    # Include app URLs - No namespace parameters, let app_name handle it
    path('provider/', include('provider.urls')),
    path('patient/', include('patient.urls')),
    
    # API endpoints - No namespace parameters, let app_name handle it
    path('api/', include('api.urls')),  # Main API
    path('api/patient/', include('patient.api.urls')),
    path('api/provider/', include('provider.api.urls')),
    
    # Swagger documentation URLs
    re_path(r'^api/docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Simple unauthorized page (no template needed)
    path('unauthorized/', 
         lambda request: HttpResponse("Unauthorized access. You don't have permission to access this resource.", status=403), 
         name='unauthorized'),
]
