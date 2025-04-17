# theme_name/context_processors.py

from .repositories import PatientRepository

def patient_context(request):
    """
    Add patient-related context data to all templates.
    """
    # Only attempt to get patient data if the user is authenticated
    # In mock mode, this will always get a default patient
    try:
        patient = PatientRepository.get_current(request)
        patient_name = f"{patient['first_name']} {patient['last_name']}"
        return {
            'patient': patient,
            'patient_name': patient_name,
        }
    except Exception:
        # Return empty context if there's an error
        return {}

def site_settings(request):
    """
    Add site-wide settings to all templates.
    """
    # These could eventually come from a database model
    return {
        'site_name': 'Northern Health Innovations',
        'site_tagline': 'Bold Innovations. Secure Care.',
        'contact_email': 'info@northernhealth.example.com',
        'contact_phone': '(555) 123-4567',
        'pharmacy_name': 'Northern Pharmacy',
        'pharmacy_address': '123 Health Street',
        'pharmacy_city_state_zip': 'Anytown, ST 12345',
        'pharmacy_phone': '(555) 123-4567',
    }

def navigation(request):
    """
    Add navigation context to all templates.
    """
    # This could be more dynamic based on user permissions
    return {
        'nav_sections': [
            {'name': 'dashboard', 'label': 'Dashboard', 'url': 'patient_dashboard', 'icon': '🏠'},
            {'name': 'appointments', 'label': 'Appointments', 'url': 'patient_appointments', 'icon': '📅'},
            {'name': 'prescriptions', 'label': 'Prescriptions', 'url': 'patient_prescriptions', 'icon': '💊'},
            {'name': 'email', 'label': 'Email', 'url': 'patient_email', 'icon': '📧'},
            {'name': 'messages', 'label': 'Messages', 'url': 'patient_messages', 'icon': '📧'},
            {'name': 'video', 'label': 'Jitsi Video', 'url': 'patient_jitsi', 'icon': '🎥'},
        ],
    }
