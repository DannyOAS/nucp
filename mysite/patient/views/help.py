# patient/views/help.py
# patient/views/help_views.py
from django.shortcuts import render
from patient.decorators import patient_required

# Uncomment for API-based implementation
# import requests
# from django.conf import settings
# from patient.utils import get_auth_header

@patient_required
def patient_help_center(request):
    """View for patient help center"""
    patient = request.patient
    
    # Get FAQ categories and questions
    faqs = [
        {
            'category': 'Account',
            'questions': [
                {
                    'question': 'How do I update my profile information?',
                    'answer': 'Go to Profile in the navigation menu and click Edit Profile.'
                },
                {
                    'question': 'How do I change my password?',
                    'answer': 'Go to Settings in your profile and select Change Password.'
                }
            ]
        },
        {
            'category': 'Appointments',
            'questions': [
                {
                    'question': 'How do I schedule an appointment?',
                    'answer': 'Go to Appointments and click Schedule New Appointment.'
                },
                {
                    'question': 'How do I reschedule or cancel an appointment?',
                    'answer': 'Go to Appointments, find your appointment, and click Reschedule or Cancel.'
                }
            ]
        },
        {
            'category': 'Prescriptions',
            'questions': [
                {
                    'question': 'How do I request a prescription refill?',
                    'answer': 'Go to Prescriptions, find your medication, and click Request Refill.'
                },
                {
                    'question': 'How do I view my current medications?',
                    'answer': 'Go to Prescriptions to see all your active medications.'
                }
            ]
        }
    ]
    
    context = {
        'patient': patient,
        'patient_name': patient.full_name,
        'faqs': faqs,
        'active_section': 'help_center'
    }
    
    # # Uncomment for API-based implementation
    # api_url = f"{settings.API_BASE_URL}/api/"
    # headers = get_auth_header(request)
    # 
    # try:
    #     # Get FAQs from API
    #     faqs_response = requests.get(
    #         f"{api_url}faqs/patient/",
    #         headers=headers
    #     )
    #     
    #     if faqs_response.ok:
    #         faqs = faqs_response.json()
    #     else:
    #         # Fallback to default FAQs
    #         faqs = [
    #             {
    #                 'category': 'Account',
    #                 'questions': [
    #                     {
    #                         'question': 'How do I update my profile information?',
    #                         'answer': 'Go to Profile in the navigation menu and click Edit Profile.'
    #                     },
    #                     {
    #                         'question': 'How do I change my password?',
    #                         'answer': 'Go to Settings in your profile and select Change Password.'
    #                     }
    #                 ]
    #             },
    #             # Other default categories...
    #         ]
    #     
    #     context = {
    #         'patient': patient,
    #         'patient_name': patient.full_name,
    #         'faqs': faqs,
    #         'active_section': 'help_center'
    #     }
    # except Exception as e:
    #     messages.warning(request, f"Error loading help center content: {str(e)}")
    
    return render(request, 'patient/help_center.html', context)
