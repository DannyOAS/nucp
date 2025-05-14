# patient/apps.py
from django.apps import AppConfig


class PatientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patient'
    
    def ready(self):
        """Connect signal handlers when the app is ready"""
        import patient.signals
