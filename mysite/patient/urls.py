from django.urls import path
from . import views

app_name = 'patient'

urlpatterns = [
    # Dashboard
    path('', views.patient_dashboard, name='patient_dashboard'),
    
    # Profile related pages
    path('profile/', views.patient_profile, name='patient_profile'),
    path('medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('help-center/', views.patient_help_center, name='patient_help_center'),
    path('search/', views.patient_search, name='patient_search'),

    # Appointment URLs  
    path('appointments/', views.appointments_view, name='patient_appointments'),
    path('appointments/schedule/', views.schedule_appointment, name='schedule_appointment'),
    path('appointments/reschedule/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),

    # Email URLs
    path('email/', views.email_view, name='patient_email'),
    path('email/compose/', views.compose_email, name='patient_compose_email'),
    path('email/folder/<str:folder>/', views.email_folder, name='patient_email_folder'),
    path('email/view/<int:message_id>/', views.view_email, name='patient_view_message'),
    path('email/action/<int:message_id>/<str:action>/', views.email_action, name='patient_message_action'),
    
    # Video
    path('jitsi-video/', views.jitsi_video_view, name='patient_jitsi'),
    path('jitsi-video/join/<int:appointment_id>/', views.join_video_appointment, name='join_video_appointment'),
    
    # Prescriptions
    path('prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('prescriptions/request/', views.request_prescription, name='request_prescription'),
    path('prescriptions/refill/<int:prescription_id>/', views.request_refill, name='request_refill'),
    path('prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
]
