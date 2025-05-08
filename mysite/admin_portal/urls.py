from django.urls import path
from . import views
from .views import dashboard, logs, patients, providers

app_name = 'admin_portal'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('patients/', views.admin_patients, name='admin_patients'),
    path('providers/', views.admin_providers, name='admin_providers'),
    path('logs/', views.admin_logs, name='admin_logs'),
    
    # AI Config
    path('ai-config/', views.ai_config_dashboard, name='ai_config_dashboard'),
    path('ai-config/model/<int:config_id>/', views.edit_model_config, name='edit_model_config'),
    
    # Templates
    path('templates/', views.templates_dashboard, name='templates_dashboard'),
    path('templates/create/', views.create_template, name='create_template'),
    path('templates/<int:template_id>/edit/', views.edit_template, name='edit_template'),
]
