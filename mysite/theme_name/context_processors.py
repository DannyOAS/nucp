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
        
        # NUCP general info
        'nucp_name': 'NUCP™',
        'nucp_fullname': 'Norhi Unified Care Platform',
        'nucp_tagline': 'Redefining Healthcare Technology',
        'nucp_description': 'A comprehensive healthcare solution designed by physicians for optimal clinical workflow.',
        'company_address': '5600-100 King Street West, Toronto, ON, M5X 1A9',
        'company_email': 'info@norhi.ca',
        
        # Colors and styling
        'primary_color': '#004d40',
        'hover_color': '#00332e',
        'light_bg': '#edf7f5',
        'gradient': 'linear-gradient(to right, #004d40, #00695c)',
        
        # Core features
        'nucp_features': [
            {
                'title': 'AI Scribe',
                'description': 'Voice-to-text with LLM assistance',
                'icon_type': 'microphone'
            },
            {
                'title': 'PHIPA Compliant',
                'description': 'Secure messaging & video',
                'icon_type': 'lock'
            },
            {
                'title': 'Smart Forms',
                'description': 'Automated medical documentation',
                'icon_type': 'document'
            },
            {
                'title': 'Seamless Care',
                'description': 'Interoperable health records',
                'icon_type': 'users'
            }
        ],
        
        # Detailed features
        'provider_features': [
            {
                'title': 'AI-Powered Scribe',
                'description': 'Transform your clinical documentation with voice-to-text LLM technology that captures patient encounters with unprecedented accuracy and efficiency.',
                'icon_type': 'microphone',
                'benefits': [
                    'Automatic transcription of patient visits',
                    'Smart formatting into SOAP notes',
                    'AI-suggested follow-up questions'
                ]
            },
            {
                'title': 'Automated Documentation',
                'description': 'Generate professional medical forms in seconds with intelligent templates that adapt to your specific needs and integrate with your workflow.',
                'icon_type': 'document',
                'benefits': [
                    'Lab requisitions with one click',
                    'Smart sick notes and referrals',
                    'Insurance forms pre-populated'
                ]
            },
            {
                'title': 'Secure Communication',
                'description': 'Connect with patients and colleagues through PHIPA-compliant messaging, video conferencing, and seamless information sharing.',
                'icon_type': 'lock',
                'benefits': [
                    'End-to-end encrypted messaging',
                    'HD video consultations',
                    'Secure document sharing'
                ]
            }
        ],
        
        # Patient portal features
        'patient_features': [
            {
                'title': 'Secure Messaging',
                'description': 'Communicate directly with your healthcare providers through encrypted messaging.'
            },
            {
                'title': 'Virtual Consultations',
                'description': 'Connect with your doctor from anywhere through high-quality video calls.'
            },
            {
                'title': 'Prescription Management',
                'description': 'Request refills, view medication details, and get timely reminders.'
            }
        ],
        
        # Partners
        'partners': [
            {'name': 'Partner 1'},
            {'name': 'Partner 2'},
            {'name': 'Partner 3'},
            {'name': 'Partner 4'}
        ],
        
        # Copyright and legal
        'footer_year': '2025',
        'company_full_name': 'Northern Health Innovations Inc.',
        'copyright_text': '© 2025 Northern Health Innovations Inc. All rights reserved.'
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
