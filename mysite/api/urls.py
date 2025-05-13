# api/urls.py
from django.urls import path, include

urlpatterns = [
    path('provider/', include('provider.api.urls')),
    # Future apps will be added here
    # path('patient/', include('patient.api.urls')),
    # path('admin/', include('admin_portal.api.urls')),
]
