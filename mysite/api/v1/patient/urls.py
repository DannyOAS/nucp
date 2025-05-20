# patient/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet, AppointmentViewSet, PrescriptionViewSet,
    PrescriptionRequestViewSet, MessageViewSet
)

app_name = 'patient_api'  # Add this line

router = DefaultRouter()
router.register(r'profile', PatientViewSet, basename='patient-profile')
router.register(r'appointments', AppointmentViewSet, basename='patient-appointments')
router.register(r'prescriptions', PrescriptionViewSet, basename='patient-prescriptions')
router.register(r'prescription-requests', PrescriptionRequestViewSet, basename='patient-prescription-requests')
router.register(r'messages', MessageViewSet, basename='patient-messages')

urlpatterns = [
    path('', include(router.urls)),
]
