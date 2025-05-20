# api/v1/urls.py
from django.urls import include, path

urlpatterns = [
    # Include all v1 endpoints
    path('', include('api.v1.core.urls')),  # Core API (users, groups)
    path('patient/', include('api.v1.patient.urls')),  # Patient API
    path('provider/', include('api.v1.provider.urls')),  # Provider API
]
