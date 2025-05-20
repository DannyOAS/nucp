# provider/services/__init__.py
# Import existing services
from .provider_service import ProviderService
from .patient_service import PatientService
from .prescription_service import PrescriptionService
from .appointment_service import AppointmentService
from .message_service import MessageService
from .video_service import VideoService
from .form_automation_service import FormAutomationService

# Add the missing import
from .ai_configuration_service import AIConfigurationService
