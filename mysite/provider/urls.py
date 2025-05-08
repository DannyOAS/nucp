# provider/urls.py
from django.urls import path
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
    
    # Video consultation
    path('video-consultation/', views.provider_video_consultation, name='provider_video_consultation'),

    # Appointments
    path('appointments/', views.provider_appointments, name='provider_appointments'),
    path('appointments/schedule/', views.schedule_appointment, name='provider_schedule_appointment'),
    path('appointments/view/<int:appointment_id>/', views.view_appointment, name='view_appointment'),
    path('appointments/reschedule/<int:appointment_id>/', views.reschedule_appointment, name='provider_reschedule_appointment'),
    path('appointments/status/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),

    # Messages
    path('messages/', views.provider_messages, name='provider_messages'),
    path('messages/sent/', views.provider_sent_messages, name='provider_sent_messages'),
    path('messages/view/<int:message_id>/', views.provider_view_message, name='provider_view_message'),
    path('messages/compose/', views.provider_compose_message, name='provider_compose_message'),
    path('messages/action/<int:message_id>/<str:action>/', views.provider_message_action, name='provider_message_action'),

    # Email
    path('email/', views.provider_email, name='provider_email'),
    path('email/view/<int:message_id>/', views.provider_view_message, name='provider_view_message'),
    path('email/compose/', views.provider_compose_message, name='provider_compose_message'),
    path('email/action/<int:message_id>/<str:action>/', views.provider_message_action, name='provider_message_action'),
    path('email/templates/', views.load_templates, name='load_templates'),
    
    # Temporarily comment out AI Scribe URLs
    path('ai-scribe/', views.ai_scribe_dashboard, name='ai_scribe_dashboard'),
    path('ai-scribe/start-recording/', views.start_recording, name='start_recording'),
    path('ai-scribe/stop-recording/', views.stop_recording, name='stop_recording'),
    path('ai-scribe/transcription/<int:recording_id>/', views.get_transcription, name='get_transcription'),
    path('ai-scribe/generate-note/<int:transcription_id>/', views.generate_clinical_note, name='generate_clinical_note'),
    path('ai-scribe/notes/<int:note_id>/', views.view_clinical_note, name='view_clinical_note'),
    path('ai-scribe/notes/<int:note_id>/edit/', views.edit_clinical_note, name='edit_clinical_note'),
    
    # Temporarily comment out Forms URLs
    path('forms/', views.forms_dashboard, name='forms_dashboard'),
    path('forms/create/<int:template_id>/', views.create_form, name='create_form'),
    path('forms/document/<int:document_id>/', views.view_document, name='view_document'),
    path('forms/document/<int:document_id>/pdf/', views.download_document_pdf, name='download_document_pdf'),
    path('forms/document/<int:document_id>/status/', views.update_document_status, name='update_document_status'),
]

