# admin_portal/views/__init__.py
from .dashboard import admin_dashboard
from .logs import logs_dashboard, ai_usage_logs, user_activity_logs
from .patients import patients_list, patient_detail
from .providers import providers_list, provider_detail, add_provider

# Add aliases for the URL patterns
admin_patients = patients_list
admin_providers = providers_list
admin_logs = logs_dashboard

# Import AI-related views from common app
from common.views.ai_views.config import ai_config_dashboard, edit_model_config
from common.views.ai_views.forms import templates_dashboard, create_template, edit_template
