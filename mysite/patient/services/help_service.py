# patient/services/help_service.py

class HelpService:
    """Service layer for patient help center operations"""
    
    @staticmethod
    def get_help_center_data():
        """
        Get help center data including FAQs and support contact info
        
        Returns:
            dict: Dictionary containing help center data
        """
        try:
            # In a real implementation, this might come from a database
            # or external content management system
            
            # FAQ categories
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
            
            # Support contact information
            support_contact = {
                'email': 'support@example.com',
                'phone': '1-800-123-4567',
                'hours': 'Monday - Friday, 9:00 AM - 5:00 PM'
            }
            
            return {
                'success': True,
                'faqs': faqs,
                'support_contact': support_contact
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'faqs': [],
                'support_contact': {}
            }
