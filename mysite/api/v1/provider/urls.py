# mysite/api/v1/provider/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProviderViewSet, AppointmentViewSet, PrescriptionViewSet,
    ClinicalNoteViewSet, DocumentTemplateViewSet, GeneratedDocumentViewSet,
    RecordingSessionViewSet, ProviderPatientsViewSet, MessageViewSet
)

app_name = 'provider_api_v1'

router = DefaultRouter()
router.register(r'profile', ProviderViewSet, basename='provider-profile')
router.register(r'appointments', AppointmentViewSet, basename='provider-appointments')
router.register(r'prescriptions', PrescriptionViewSet, basename='provider-prescriptions')
router.register(r'clinical-notes', ClinicalNoteViewSet, basename='provider-clinical-notes')
router.register(r'document-templates', DocumentTemplateViewSet, basename='provider-document-templates')
router.register(r'generated-documents', GeneratedDocumentViewSet, basename='provider-generated-documents')
router.register(r'recordings', RecordingSessionViewSet, basename='provider-recordings')
router.register(r'templates', DocumentTemplateViewSet, basename='provider-templates')
router.register(r'documents', GeneratedDocumentViewSet, basename='provider-documents')
router.register(r'patients', ProviderPatientsViewSet, basename='provider-patients')
router.register(r'messages', MessageViewSet, basename='provider-messages')

urlpatterns = [
    path('', include(router.urls)),
]
