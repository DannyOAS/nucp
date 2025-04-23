from django.contrib import admin
from django.urls import path, include
from .views import home, about, contact, blog_list, blog_detail
from django.views.generic.base import RedirectView
from . import views
from django.contrib.auth import views as auth_views

# Main website URLs
website_urls = [
    path("", home, name="home"),
    path('admin/', admin.site.urls),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
    path("blog/", blog_list, name="blog_list"),  # Blog list page
    path("blog/<int:pk>/", blog_detail, name="blog_detail"),  # Blog detail page
    path("nucp/", RedirectView.as_view(url="https://nucp.ca", permanent=True), name="nucp"),
    path('registration/', views.registration_view, name='registration'),
    path('prescription/', views.prescription_view, name='prescription'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_selection, name='register_selection'),
    path('register/patient/', views.patient_registration, name='patient_registration'),
    path('register/provider/', views.provider_registration, name='provider_registration'),
    path('registration/success/', views.registration_success, name='registration_success'),
    path('schedule-demo/', views.schedule_demo, name='schedule_demo'),
]

# Provider dashboard URLs
provider_urls = [
    path('provider-dashboard/', views.provider_dashboard, name='provider_dashboard'),
    # Provider profile pages
    path('provider-dashboard/profile/', views.provider_profile, name='provider_profile'),
    path('provider-dashboard/settings/', views.provider_settings, name='provider_settings'),
    path('provider-dashboard/help-support/', views.provider_help_support, name='provider_help_support'),

    path('provider-dashboard/patients/', views.provider_patients, name='provider_patients'),
    path('provider-dashboard/patients/add/', views.add_patient, name='add_patient'),
    path('provider-dashboard/patients/<int:patient_id>/', views.view_patient, name='view_patient'),
    path('provider-dashboard/prescriptions/', views.provider_prescriptions, name='provider_prescriptions'),
    path('provider-dashboard/video-consultation/', views.provider_video_consultation, name='provider_video_consultation'),
    path('provider-dashboard/appointments/', views.provider_appointments, name='provider_appointments'),

    # Provider messaging URLs
    path('provider-dashboard/messages/', views.provider_messages, name='provider_messages'),
    path('provider-dashboard/messages/sent/', views.provider_sent_messages, name='provider_sent_messages'),
    path('provider-dashboard/messages/view/<int:message_id>/', views.provider_view_message, name='provider_view_message'),
    path('provider-dashboard/messages/compose/', views.provider_compose_message, name='provider_compose_message'),
    path('provider-dashboard/messages/action/<int:message_id>/<str:action>/', views.provider_message_action, name='provider_message_action'),
# Prescription management URLs
    path('provider-dashboard/prescriptions/approve/<int:prescription_id>/', views.approve_prescription, name='approve_prescription'),
    path('provider-dashboard/prescriptions/review/<int:prescription_id>/', views.review_prescription, name='review_prescription'),
    path('provider-dashboard/prescriptions/create/', views.create_prescription, name='create_prescription'),
    path('provider-dashboard/prescriptions/edit/<int:prescription_id>/', views.edit_prescription, name='edit_prescription'),
]

# Patient dashboard URLs
#patient_urls = [
#    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
#    path('patient-dashboard/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
#    path('patient-dashboard/prescriptions/request/', views.request_prescription, name='request_prescription'),
#    path('patient-dashboard/prescriptions/refill/<int:prescription_id>/', views.request_refill, name='request_refill'),
#    path('patient-dashboard/prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
#]

# Patient dashboard URLs
# Patient dashboard URLs
patient_urls = [
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    # Patient profile related pages
    path('patient-dashboard/profile/', views.patient_profile, name='patient_profile'),
    path('patient-dashboard/medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('patient-dashboard/help-center/', views.patient_help_center, name='patient_help_center'),
    path('logout/', views.logout_view, name='logout'),

    path('patient-dashboard/search/', views.patient_search, name='patient_search'),
    path('patient-dashboard/appointments/', views.appointments_view, name='patient_appointments'),
    path('patient-dashboard/email/', views.email_view, name='patient_email'),
#    path('patient-dashboard/messages/', views.messages_view, name='patient_messages'),
    # Patient messaging URLs
    path('patient-dashboard/messages/', views.patient_messages, name='patient_messages'),
    path('patient-dashboard/messages/sent/', views.patient_sent_messages, name='patient_sent_messages'),
    path('patient-dashboard/messages/archived/', views.patient_archived_messages, name='patient_archived_messages'),
    path('patient-dashboard/messages/view/<int:message_id>/', views.patient_view_message, name='patient_view_message'),
    path('patient-dashboard/messages/compose/', views.patient_compose_message, name='patient_compose_message'),
    path('patient-dashboard/messages/action/<int:message_id>/<str:action>/', views.patient_message_action, name='patient_message_action'),

    path('patient-dashboard/jitsi-video/', views.jitsi_video_view, name='patient_jitsi'),
    path('patient-dashboard/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient-dashboard/prescriptions/request/', views.request_prescription, name='request_prescription'),
    path('patient-dashboard/prescriptions/refill/<int:prescription_id>/', views.request_refill, name='request_refill'),
    path('patient-dashboard/prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
]
# Authentication URLs
admin_urls = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/patients/', views.admin_patients, name='admin_patients'),
    path('admin-dashboard/providers/', views.admin_providers, name='admin_providers'),
    path('admin-dashboard/logs/', views.admin_logs, name='admin_logs'),
    path('admin-dashboard/ai-config/', views.ai_config_dashboard, name='ai_config_dashboard'),
]
#===============================================New added URLS+===============================================

# Provider-specific URLs for AI Scribe
ai_scribe_urls = [
    path('provider/ai-scribe/', views.ai_scribe_dashboard, name='ai_scribe_dashboard'),
    path('provider/ai-scribe/start-recording/', views.start_recording, name='start_recording'),
    path('provider/ai-scribe/stop-recording/', views.stop_recording, name='stop_recording'),
    path('provider/ai-scribe/transcription/<int:recording_id>/', views.get_transcription, name='get_transcription'),
    path('provider/ai-scribe/generate-note/<int:transcription_id>/', views.generate_clinical_note, name='generate_clinical_note'),
    path('provider/ai-scribe/notes/<int:note_id>/', views.view_clinical_note, name='view_clinical_note'),
    path('provider/ai-scribe/notes/<int:note_id>/edit/', views.edit_clinical_note, name='edit_clinical_note'),
]

# Provider-specific URLs for Form Automation
forms_urls = [
    path('provider/forms/', views.forms_dashboard, name='forms_dashboard'),
    path('provider/forms/create/<int:template_id>/', views.create_form, name='create_form'),
    path('provider/forms/document/<int:document_id>/', views.view_document, name='view_document'),
    path('provider/forms/document/<int:document_id>/pdf/', views.download_document_pdf, name='download_document_pdf'),
    path('provider/forms/document/<int:document_id>/status/', views.update_document_status, name='update_document_status'),
]

# Admin-specific URLs for AI Configuration
admin_ai_urls = [
    path('admin-dashboard/ai-config/', views.ai_config_dashboard, name='ai_config_dashboard'),
    path('admin-dashboard/ai-config/model/<int:config_id>/', views.edit_model_config, name='edit_model_config'),
    path('admin-dashboard/templates/', views.templates_dashboard, name='templates_dashboard'),
    path('admin-dashboard/templates/create/', views.create_template, name='create_template'),
    path('admin-dashboard/templates/<int:template_id>/edit/', views.edit_template, name='edit_template'),
]

# Combine all URL patterns
#urlpatterns = ai_scribe_urls + forms_urls + admin_ai_urls

# Combine all URL patterns
urlpatterns = website_urls + provider_urls + patient_urls + admin_urls + ai_scribe_urls + forms_urls + admin_ai_urls
# To include admin URLs later, you can uncomment and add: urlpatterns += admin_urls
