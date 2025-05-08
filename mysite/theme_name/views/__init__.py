# Import all views for backward compatibility

# Main website views
from .main_views import home, about, contact, blog_list, blog_detail, privacy_policy, terms_of_use, schedule_demo

# Registration views
from .registration_views import (
    registration_view, prescription_view, login_view, 
    register_selection, patient_registration, provider_registration, 
    registration_success, schedule_demo, logout_view
)
