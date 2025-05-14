# provider/urls.py
from django.urls import path, include
from . import views

app_name = 'provider'

urlpatterns = [
    # Dashboard
    path('', views.provider_dashboard, name='provider_dashboard'),
    
    # Profile pages
    path('profile/', views.provider_profile, name='provider_profile'),
    path('settings/', views.provider_settings, name='provider_settings'),
    path('help-support/', views.provider_help_support, name='provider_help_support'),

    # Patient management
    path('patients/', views.provider_patients, name='provider_patients'),
    path('patients/add/', views.add_patient, name='add_patient'),
    path('patients/<int:patient_id>/', views.view_patient, name='view_patient'),
    
    # Prescriptions
    path('prescriptions/', views.provider_prescriptions, name='provider_prescriptions'),
    path('prescriptions/approve/<int:prescription_id>/', views.approve_prescription, name='approve_prescription'),
    path('prescriptions/review/<int:prescription_id>/', views.review_prescription, name='review_prescription'),
    path('prescriptions/create/', views.create_prescription, name='create_prescription'),
    path('prescriptions/edit/<int:prescription_id>/', views.edit_prescription, name='edit_prescription'),
    
    # Appointments
    path('appointments/', views.provider_appointments, name='provider_appointments'),
    path('appointments/schedule/', views.schedule_appointment, name='provider_schedule_appointment'),
    path('appointments/view/<int:appointment_id>/', views.view_appointment, name='view_appointment'),
    path('appointments/reschedule/<int:appointment_id>/', views.reschedule_appointment, name='provider_reschedule_appointment'),
    path('appointments/status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),

    # Email and Messages
    path('messages/', views.provider_email, name='provider_messages'),  # Backward compatibility
    path('email/', views.provider_email, name='provider_email'),
    path('email/view/<int:message_id>/', views.provider_view_message, name='provider_view_message'),
    path('email/compose/', views.provider_compose_message, name='provider_compose_message'),
    path('email/action/<int:message_id>/<str:action>/', views.provider_message_action, name='provider_message_action'),
    path('email/templates/', views.load_templates, name='load_templates'),
    
    # Video Consultation
    path('video-consultation/', views.provider_video_consultation, name='provider_video_consultation'),
    path('video-consultation/start-recording/<int:appointment_id>/', views.start_recording, name='start_recording'),
    path('video-consultation/stop-recording/<int:recording_id>/', views.stop_recording, name='stop_recording'),
    path('video-consultation/view-recording/<int:recording_id>/', views.view_recording, name='view_recording'),
    
    # AI Scribe views - Updated to use proper module import
    path('ai-scribe/', views.ai_views_scribe.ai_scribe_dashboard, name='ai_scribe_dashboard'),
    path('ai-scribe/start-recording/', views.ai_views_scribe.start_recording, name='ai_start_recording'),
    path('ai-scribe/stop-recording/', views.ai_views_scribe.stop_recording, name='ai_stop_recording'),
    path('ai-scribe/transcription/<int:recording_id>/', views.ai_views_scribe.get_transcription, name='get_transcription'),
    path('ai-scribe/generate-note/<int:transcription_id>/', views.ai_views_scribe.generate_clinical_note, name='generate_clinical_note'),
    path('ai-scribe/notes/<int:note_id>/', views.ai_views_scribe.view_clinical_note, name='view_clinical_note'),
    path('ai-scribe/notes/<int:note_id>/edit/', views.ai_views_scribe.edit_clinical_note, name='edit_clinical_note'),

    # AI Configuration views
    path('ai-scribe/config/', views.ai_views_config.ai_config_dashboard, name='ai_config_dashboard'),
    path('ai-scribe/config/edit/<int:config_id>/', views.ai_views_config.edit_model_config, name='edit_model_config'),
    path('ai-scribe/config/create/', views.ai_views_config.create_model_config, name='create_model_config'),
    path('ai-scribe/config/toggle/<int:config_id>/', views.ai_views_config.toggle_model_status, name='toggle_model_status'),
    path('ai-scribe/config/test/<int:config_id>/', views.ai_views_config.test_model_config, name='test_model_config'),
    
    # Forms views
    path('forms/', views.ai_views_forms.forms_dashboard, name='forms_dashboard'),
    path('forms/create/<int:template_id>/', views.ai_views_forms.create_form, name='create_form'),
    path('forms/document/<int:document_id>/', views.ai_views_forms.view_document, name='view_document'),
    path('forms/document/<int:document_id>/pdf/', views.ai_views_forms.download_document_pdf, name='download_document_pdf'),
    path('forms/document/<int:document_id>/status/', views.ai_views_forms.update_document_status, name='update_document_status'),
    
    # Templates management views (admin only)
    path('templates/', views.ai_views_forms.templates_dashboard, name='templates_dashboard'),
    path('templates/create/', views.ai_views_forms.create_template, name='create_template'),
    path('templates/edit/<int:template_id>/', views.ai_views_forms.edit_template, name='edit_template'),
    
    # API endpoints
    path('api/', include('provider.api.urls')),
]
