from django.urls import path
from . import views
#from .views import appointments, dashboard, messages, prescriptions, profile, video

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

    # Email (keeping email, removing message URLs)
    path('email/', views.email_view, name='patient_email'),
    
    # Removed message URLs
    
    # Video
    path('jitsi-video/', views.jitsi_video_view, name='patient_jitsi'),
    
    # Prescriptions
    path('prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('prescriptions/request/', views.request_prescription, name='request_prescription'),
    path('prescriptions/refill/<int:prescription_id>/', views.request_refill, name='request_refill'),
    path('prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
]
