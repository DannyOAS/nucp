# mysite/api/v1/urls.py
from django.urls import include, path
from rest_framework.authtoken import views as token_views

urlpatterns = [
    # Include all v1 endpoints
    path('', include('api.v1.core.urls')),  # Core API (users, groups)
    path('patient/', include('api.v1.patient.urls')),  # Patient API
    path('provider/', include('api.v1.provider.urls')),  # Provider API
    path('auth/', include('rest_framework.urls')),
    path('token-auth/', token_views.obtain_auth_token, name='api-token-auth'),
]
