# mock_models.py
from datetime import datetime, timedelta
from . import data_access

class MockQuerySet:
    def __init__(self, data):
        self.data = data
    
    def filter(self, **kwargs):
        # Simple filtering implementation
        filtered_data = self.data
        for key, value in kwargs.items():
            # Handle special cases like field__contains
            if '__' in key:
                field, op = key.split('__', 1)
                if op == 'contains':
                    filtered_data = [item for item in filtered_data if value.lower() in str(getattr(item, field, '')).lower()]
                elif op == 'exact':
                    filtered_data = [item for item in filtered_data if getattr(item, field, '') == value]
                elif op == 'gt':
                    filtered_data = [item for item in filtered_data if getattr(item, field, 0) > value]
                elif op == 'lt':
                    filtered_data = [item for item in filtered_data if getattr(item, field, 0) < value]
                elif op == 'gte':
                    filtered_data = [item for item in filtered_data if getattr(item, field, 0) >= value]
                elif op == 'lte':
                    filtered_data = [item for item in filtered_data if getattr(item, field, 0) <= value]
            else:
                filtered_data = [item for item in filtered_data if getattr(item, key, None) == value]
        return MockQuerySet(filtered_data)
    
    def order_by(self, field):
        reverse = False
        if field.startswith('-'):
            field = field[1:]
            reverse = True
        sorted_data = sorted(self.data, key=lambda x: getattr(x, field, ''), reverse=reverse)
        return MockQuerySet(sorted_data)
    
    def first(self):
        """Return first item or None."""
        return self.data[0] if self.data else None
    
    def last(self):
        """Return last item or None."""
        return self.data[-1] if self.data else None
    
    def all(self):
        """Return copy of the queryset."""
        return MockQuerySet(self.data.copy())
    
    def exclude(self, **kwargs):
        """Exclude items matching conditions."""
        result = self.data.copy()
        for key, value in kwargs.items():
            if '__' in key:
                field, op = key.split('__', 1)
                if op == 'contains':
                    result = [item for item in result if value.lower() not in str(getattr(item, field, '')).lower()]
            else:
                result = [item for item in result if getattr(item, key, None) != value]
        return MockQuerySet(result)
    
    def count(self):
        """Return count of items."""
        return len(self.data)
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            return MockQuerySet(self.data[key])
        return self.data[key]
    
    def exists(self):
        """Return True if queryset contains any results."""
        return len(self.data) > 0


# Base mock model class
class MockModel:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
    
    def save(self):
        """Simulate saving the model."""
        # In a real implementation, you might update the underlying data 
        # This is just a placeholder for now
        pass
    
    def delete(self):
        """Simulate deleting the model."""
        # In a real implementation, you might remove from the underlying data 
        # This is just a placeholder for now
        pass


# Patient mock model
class MockPatient(MockModel):
    @classmethod
    def objects(cls):
        patient_data = data_access.get_all_patients(use_mock=True)
        patients = [cls(p) for p in patient_data]
        return MockQuerySet(patients)
    
    @classmethod
    def get_current(cls, request):
        """Get the current patient from request."""
        patient_data = data_access.get_current_patient(request, use_mock=True)
        return cls(patient_data)


# Prescription mock model
class MockPrescription(MockModel):
    @classmethod
    def objects(cls):
        prescription_data = data_access.get_all_prescriptions(use_mock=True)
        prescriptions = [cls(p) for p in prescription_data]
        return MockQuerySet(prescriptions)
    
    @classmethod
    def get_active_for_patient(cls, patient_id):
        """Get active prescriptions for a patient."""
        all_prescriptions = cls.objects()
        # In a real model, you would filter by patient_id
        # For now, we'll just filter by status
        return all_prescriptions.filter(status="Active")
    
    @classmethod
    def get_historical_for_patient(cls, patient_id):
        """Get historical prescriptions for a patient."""
        all_prescriptions = cls.objects()
        # In a real model, you would filter by patient_id and status
        # For now, we'll just exclude active prescriptions
        return all_prescriptions.exclude(status="Active")
    
    @classmethod
    def get_by_id(cls, prescription_id):
        """Get prescription by ID."""
        prescription_data = data_access.get_prescription_by_id(prescription_id, use_mock=True)
        if prescription_data:
            return cls(prescription_data)
        return None
    
    @classmethod
    def create(cls, data):
        """Create a new prescription."""
        prescription_data = data_access.save_prescription_request(data, use_mock=True)
        return cls(prescription_data)


# Appointment mock model
class MockAppointment(MockModel):
    @classmethod
    def objects(cls):
        appointment_data = data_access.get_all_appointments(use_mock=True)
        appointments = [cls(a) for a in appointment_data]
        return MockQuerySet(appointments)
    
    @classmethod
    def get_upcoming_for_patient(cls, patient_id):
        """Get upcoming appointments for a patient."""
        all_appointments = cls.objects()
        # In a real model, you would filter by patient_id and date > today
        # For now, we'll just exclude appointments with "Completed" status
        return all_appointments.exclude(status="Completed") if hasattr(all_appointments.first(), 'status') else all_appointments
    
    @classmethod
    def get_past_for_patient(cls, patient_id):
        """Get past appointments for a patient."""
        all_appointments = cls.objects()
        # In a real model, you would filter by patient_id and date < today
        # For now, we'll just filter for appointments with "Completed" status
        return all_appointments.filter(status="Completed") if hasattr(all_appointments.first(), 'status') else MockQuerySet([])
    
    @classmethod
    def get_by_id(cls, appointment_id):
        """Get appointment by ID."""
        appointment_data = data_access.get_appointment_by_id(appointment_id, use_mock=True)
        if appointment_data:
            return cls(appointment_data)
        return None


# Message mock model
class MockMessage(MockModel):
    @classmethod
    def objects(cls):
        message_data = data_access.get_all_messages(use_mock=True)
        messages = [cls(m) for m in message_data]
        return MockQuerySet(messages)
    
    @classmethod
    def get_unread_for_patient(cls, patient_id):
        """Get unread messages for a patient."""
        all_messages = cls.objects()
        # Filter to only unread messages
        return all_messages.filter(read=False)
    
    @classmethod
    def get_read_for_patient(cls, patient_id):
        """Get read messages for a patient."""
        all_messages = cls.objects()
        # Filter to only read messages
        return all_messages.filter(read=True)
    
    @classmethod
    def get_by_id(cls, message_id):
        """Get message by ID."""
        message_data = data_access.get_message_by_id(message_id, use_mock=True)
        if message_data:
            return cls(message_data)
        return None
