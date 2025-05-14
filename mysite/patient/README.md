# Patient App

## Overview
The patient app handles all patient-facing functionality in the healthcare system, including:
- Dashboard
- Profile management
- Appointment scheduling and management
- Prescription requests and refills
- Messaging with healthcare providers
- Video consultations

## Architecture
The app follows an API-first design, with the following components:

### Models
- `Patient`: Patient profile linked to Django User
- `PrescriptionRequest`: Requests for new prescriptions or refills

### Views
Organized by functionality:
- `dashboard_views.py`: Main dashboard
- `appointment_views.py`: Appointment management
- `prescription_views.py`: Prescription management
- `messaging_views.py`: Patient-provider messaging
- `profile_views.py`: Profile management
- `video_views.py`: Video consultation
- `email_views.py`: Email communication
- `search_views.py`: Search functionality
- `help_views.py`: Help center

### Services
Business logic layer:
- `appointment_service.py`: Appointment-related logic
- `prescription_service.py`: Prescription-related logic
- `message_service.py`: Messaging-related logic
- `video_service.py`: Video consultation logic

### API
RESTful API endpoints:
- `serializers.py`: Data serialization
- `views.py`: API views and viewsets
- `urls.py`: API URL routing
- `permissions.py`: API permissions
- `filters.py`: API filtering

## API-First Approach
The app is designed with an API-first approach, where:
1. All functionality is available through API endpoints
2. Web views consume the API (currently commented out)
3. Web views use direct ORM access as a temporary measure

To transition to full API usage, uncomment the API code in each view file and comment out the direct ORM access code.
