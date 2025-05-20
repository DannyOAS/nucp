# NUCP API Documentation
#  python manage.py generate_api_docs --app api.v1.patient --output docs/patient_api.md
## Overview

The Healthcare Portal API provides a comprehensive set of endpoints for managing healthcare data, including patient records, provider information, appointments, prescriptions, and messaging. The API follows RESTful principles and uses standard HTTP methods for communication.

## Base URL

```
https://yourdomain.com/api/v1/
```

## Authentication

The API uses token-based authentication. Include your token in the Authorization header:

```
Authorization: Token <your_token>
```

To obtain a token, use the token-auth endpoint:

```
POST /api/v1/token-auth/
```

With the following payload:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

## API Versioning

This documentation covers version 1 of the API (v1). The version is specified in the URL path and is also included in response payloads:

```json
{
  "data": {},
  "api_version": "v1"
}
```

## Response Format

All responses are in JSON format. Paginated responses follow this structure:

```json
{
  "count": 42,
  "next": "https://yourdomain.com/api/v1/resource/?page=2",
  "previous": null,
  "results": [ ... ],
  "api_version": "v1"
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes and error messages:

```json
{
  "detail": "Error message explaining the issue"
}
```

Common status codes:
- 400: Bad Request - Invalid input or parameters
- 401: Unauthorized - Missing or invalid authentication
- 403: Forbidden - Authentication successful but insufficient permissions
- 404: Not Found - Resource does not exist
- 500: Internal Server Error - Server-side error

## Rate Limiting

API requests are subject to rate limiting to ensure service stability:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

## Provider Endpoints

### Provider Profile

```
GET /api/v1/provider/profile/
```

Retrieves the profile information for the authenticated provider.

**Response Example:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 4,
      "user": {
        "id": 5,
        "username": "provider1",
        "first_name": "Dr.",
        "last_name": "John Smith",
        "email": "provider1@example.com"
      },
      "license_number": "TMP5",
      "specialty": "General",
      "bio": "Experienced general practitioner with 15 years of practice.",
      "phone": "",
      "is_active": true,
      "full_name": "Dr. John Smith"
    }
  ],
  "api_version": "v1"
}
```

### Provider's Patients

```
GET /api/v1/provider/patients/
```

Retrieves a list of patients assigned to the authenticated provider.

**Parameters:**
- `search` (optional): Search by patient name
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response Example:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 2,
        "username": "patient1",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "patient1@example.com"
      },
      "date_of_birth": "1985-05-15",
      "ohip_number": "1234567890",
      "primary_phone": "555-123-4567",
      "alternate_phone": "",
      "address": "123 Main St, Toronto, ON",
      "emergency_contact_name": "John Doe",
      "emergency_contact_phone": "555-987-6543",
      "primary_provider": 4,
      "full_name": "Jane Doe"
    },
    {
      "id": 2,
      "user": {
        "id": 3,
        "username": "patient2",
        "first_name": "Bob",
        "last_name": "Smith",
        "email": "patient2@example.com"
      },
      "date_of_birth": "1990-10-20",
      "ohip_number": "0987654321",
      "primary_phone": "555-222-3333",
      "alternate_phone": "",
      "address": "456 Oak St, Toronto, ON",
      "emergency_contact_name": "Alice Smith",
      "emergency_contact_phone": "555-444-5555",
      "primary_provider": 4,
      "full_name": "Bob Smith"
    }
  ],
  "api_version": "v1"
}
```

### Provider Appointments

```
GET /api/v1/provider/appointments/
```

Retrieves appointments for the authenticated provider.

**Parameters:**
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `status` (optional): Filter by status (Scheduled, Checked In, In Progress, Completed, Cancelled, No Show)
- `type` (optional): Filter by type (Virtual, In-Person)
- `search` (optional): Search by patient name or reason
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response Example:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": 2,
      "doctor": 4,
      "time": "2025-05-21T09:30:00Z",
      "type": "Virtual",
      "status": "Scheduled",
      "reason": "Annual checkup",
      "notes": "",
      "patient_name": "Jane Doe",
      "doctor_name": "Dr. Smith"
    }
  ],
  "api_version": "v1"
}
```

#### Today's Appointments

```
GET /api/v1/provider/appointments/today/
```

Retrieves appointments scheduled for the current day.

#### Upcoming Appointments

```
GET /api/v1/provider/appointments/upcoming/
```

Retrieves the next 10 upcoming appointments.

### Provider Prescriptions

```
GET /api/v1/provider/prescriptions/
```

Retrieves prescriptions issued by the authenticated provider.

**Parameters:**
- `status` (optional): Filter by status (Pending, Active, Completed, Cancelled, Expired, Refill Requested)
- `search` (optional): Search by medication name or patient name
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response Example:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "medication_name": "Amoxicillin",
      "dosage": "500mg",
      "patient": 2,
      "doctor": 4,
      "status": "Active",
      "refills": 3,
      "refills_remaining": 2,
      "created_at": "2025-05-15T14:30:00Z",
      "updated_at": "2025-05-15T14:30:00Z",
      "patient_name": "Jane Doe"
    }
  ],
  "api_version": "v1"
}
```

#### Active Prescriptions

```
GET /api/v1/provider/prescriptions/active/
```

Retrieves active prescriptions.

#### Pending Prescriptions

```
GET /api/v1/provider/prescriptions/pending/
```

Retrieves pending prescriptions.

### Provider Messages

```
GET /api/v1/provider/messages/
```

Retrieves messages sent to or from the authenticated provider.

**Parameters:**
- `status` (optional): Filter by status (unread, read, archived, deleted, draft)
- `search` (optional): Search by subject or content
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response Example:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "sender": 2,
      "recipient": 5,
      "subject": "Question about prescription",
      "content": "Hello Dr. Smith, I have a question about my prescription...",
      "status": "unread",
      "created_at": "2025-05-15T10:00:00Z",
      "sender_name": "Jane Doe",
      "recipient_name": "Dr. John Smith"
    }
  ],
  "api_version": "v1"
}
```

#### Inbox

```
GET /api/v1/provider/messages/inbox/
```

Retrieves messages sent to the authenticated provider.

#### Sent Messages

```
GET /api/v1/provider/messages/sent/
```

Retrieves messages sent by the authenticated provider.

### Clinical Notes

```
GET /api/v1/provider/clinical-notes/
```

Retrieves clinical notes created by the authenticated provider.

```
POST /api/v1/provider/clinical-notes/
```

Creates a new clinical note.

**Request Payload:**
```json
{
  "appointment": 1,
  "provider_edited_text": "Patient presented with symptoms of...",
  "status": "Draft"
}
```

## Patient Endpoints

### Patient Profile

```
GET /api/v1/patient/profile/
```

Retrieves the profile information for the authenticated patient.

**Response Example:**
```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "patient1",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "patient1@example.com"
  },
  "date_of_birth": "1985-05-15",
  "ohip_number": "1234567890",
  "primary_phone": "555-123-4567",
  "alternate_phone": "",
  "address": "123 Main St, Toronto, ON",
  "emergency_contact_name": "John Doe",
  "emergency_contact_phone": "555-987-6543",
  "primary_provider": 4,
  "current_medications": "None",
  "allergies": "Penicillin",
  "pharmacy_details": "Healthway Pharmacy, 500 Queen St",
  "virtual_care_consent": true,
  "ehr_consent": true,
  "full_name": "Jane Doe"
}
```

#### Current Patient

```
GET /api/v1/patient/profile/me/
```

Retrieves the profile of the currently authenticated patient.

### Patient Appointments

```
GET /api/v1/patient/appointments/
```

Retrieves appointments for the authenticated patient.

**Parameters:**
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `type` (optional): Filter by type (Virtual, In-Person)
- `status` (optional): Filter by status
- `search` (optional): Search by doctor name or reason
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response Example:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": 2,
      "doctor": 4,
      "time": "2025-05-21T09:30:00Z",
      "type": "Virtual",
      "status": "Scheduled",
      "reason": "Annual checkup",
      "notes": "",
      "patient_name": "Jane Doe",
      "doctor_name": "Dr. Smith"
    }
  ],
  "api_version": "v1"
}
```

#### Upcoming Appointments

```
GET /api/v1/patient/appointments/upcoming/
```

Retrieves upcoming appointments for the authenticated patient.

#### Past Appointments

```
GET /api/v1/patient/appointments/past/
```

Retrieves past appointments for the authenticated patient.

### Patient Prescriptions

```
GET /api/v1/patient/prescriptions/
```

Retrieves prescriptions for the authenticated patient.

**Parameters:**
- `medication_name` (optional): Filter by medication name
- `status` (optional): Filter by status
- `search` (optional): Search by medication name or doctor name
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page

**Response Example:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "medication_name": "Amoxicillin",
      "dosage": "500mg",
      "instructions": "Take one tablet three times daily with food",
      "patient": 2,
      "doctor": 4,
      "status": "Active",
      "refills_remaining": 2,
      "expires": "2025-06-15",
      "created_at": "2025-05-15T14:30:00Z",
      "updated_at": "2025-05-15T14:30:00Z",
      "patient_name": "Jane Doe"
    }
  ],
  "api_version": "v1"
}
```

#### Active Prescriptions

```
GET /api/v1/patient/prescriptions/active/
```

Retrieves active prescriptions for the authenticated patient.

### Prescription Requests

```
GET /api/v1/patient/prescription-requests/
```

Retrieves prescription requests made by the authenticated patient.

```
POST /api/v1/patient/prescription-requests/
```

Creates a new prescription request.

**Request Payload:**
```json
{
  "medication_name": "Metformin",
  "current_dosage": "500mg",
  "medication_duration": "3 months",
  "last_refill_date": "2025-02-15",
  "preferred_pharmacy": "Healthway Pharmacy, 500 Queen St",
  "information_consent": true,
  "pharmacy_consent": true
}
```

**Response Example:**
```json
{
  "id": 1,
  "patient": 2,
  "medication_name": "Metformin",
  "current_dosage": "500mg",
  "medication_duration": "3 months",
  "last_refill_date": "2025-02-15",
  "preferred_pharmacy": "Healthway Pharmacy, 500 Queen St",
  "new_medical_conditions": "",
  "new_medications": "",
  "side_effects": "",
  "information_consent": true,
  "pharmacy_consent": true,
  "status": "pending",
  "created_at": "2025-05-20T14:35:00Z",
  "updated_at": "2025-05-20T14:35:00Z",
  "patient_name": "Jane Doe"
}
```

### Patient Messages

```
GET /api/v1/patient/messages/
```

Retrieves messages sent to or from the authenticated patient.

```
POST /api/v1/patient/messages/
```

Sends a new message.

**Request Payload:**
```json
{
  "recipient": 5,
  "subject": "Question about medication",
  "content": "Hello Dr. Smith, I'm having some side effects from the new medication..."
}
```

**Response Example:**
```json
{
  "id": 2,
  "sender": 2,
  "recipient": 5,
  "subject": "Question about medication",
  "content": "Hello Dr. Smith, I'm having some side effects from the new medication...",
  "status": "unread",
  "created_at": "2025-05-20T14:40:00Z",
  "sender_name": "Jane Doe",
  "recipient_name": "Dr. John Smith"
}
```

#### Inbox

```
GET /api/v1/patient/messages/inbox/
```

Retrieves messages sent to the authenticated patient.

#### Sent Messages

```
GET /api/v1/patient/messages/sent/
```

Retrieves messages sent by the authenticated patient.

## Pagination

API endpoints that return collections support pagination. The default page size is 10 items.

**Parameters:**
- `page`: Page number (starting from 1)
- `page_size`: Number of items per page (max 100)

**Response Metadata:**
- `count`: Total number of items
- `next`: URL to the next page (null if there is no next page)
- `previous`: URL to the previous page (null if there is no previous page)

## Filtering and Searching

Many endpoints support filtering and searching:

- Use query parameters named after model fields for exact matches
- Use the `search` parameter for text search across multiple fields

Example:
```
GET /api/v1/provider/appointments/?status=Scheduled&type=Virtual
```

## Best Practices

1. **Rate Limiting**: Implement client-side rate limiting to avoid hitting API limits.
2. **Caching**: Cache responses where appropriate to reduce API calls.
3. **Error Handling**: Implement robust error handling for API responses.
4. **Authentication**: Never expose API tokens in client-side code.
5. **Versioning**: Be aware of the API version you're using and check for updates.

## Support

For API support, please contact:
- Email: api-support@example.com
- Phone: 1-800-555-1234

## Legal

All data accessed through this API is subject to privacy regulations including PHIPA and HIPAA.
Unauthorized access or misuse of this API is strictly prohibited and may result in legal action.

---

© 2025 Northern Health Innovations. All rights reserved.
