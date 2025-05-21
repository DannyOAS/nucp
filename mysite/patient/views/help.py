# patient/views/help.py
from django.shortcuts import render, redirect
from django.contrib import messages
from patient.decorators import patient_required
import logging

from patient.services.help_service import HelpService
from patient.utils import get_current_patient

logger = logging.getLogger(__name__)

@patient_required
def patient_help_center(request):
    """
    Patient help center view showing FAQs and support information.
    Uses service layer for data retrieval.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get help center data from service
        help_data = HelpService.get_help_center_data()
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'faqs': help_data.get('faqs', []),
            'support_contact': help_data.get('support_contact', {}),
            'active_section': 'help_center'
        }
    except Exception as e:
        logger.error(f"Error retrieving help center data: {str(e)}")
        
        # Default FAQ categories as fallback
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
        
        support_contact = {
            'email': 'support@example.com',
            'phone': '1-800-123-4567',
            'hours': 'Monday - Friday, 9:00 AM - 5:00 PM'
        }
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'faqs': faqs,
            'support_contact': support_contact,
            'active_section': 'help_center'
        }
        messages.warning(request, "There was an issue loading the help center content. Showing default information.")
    
    return render(request, 'patient/help_center.html', context)
