# patient/services/video_service.py
from django.utils import timezone
from common.models import Appointment

class VideoService:
    @staticmethod
    def get_upcoming_video_appointments(patient):
        """Get upcoming video appointments for a patient"""
        return Appointment.objects.filter(
            patient=patient.user,
            type='Virtual',
            status='Scheduled',
            time__gte=timezone.now()
        ).order_by('time')
    
    @staticmethod
    def get_past_video_appointments(patient, limit=10):
        """Get past video appointments for a patient with optional limit"""
        return Appointment.objects.filter(
            patient=patient.user,
            type='Virtual'
        ).exclude(
            status='Scheduled'
        ).order_by('-time')[:limit]
    
    @staticmethod
    def can_join_appointment(appointment):
        """
        Check if a patient can join a video appointment
        
        Args:
            appointment: Appointment model instance
            
        Returns:
            tuple: (can_join, message)
                - can_join: Boolean indicating if patient can join
                - message: Explanation message if cannot join, or empty string
        """
        # Check if appointment is virtual
        if appointment.type != 'Virtual':
            return (False, "This is not a video appointment.")
        
        # Check appointment status
        if appointment.status != 'Scheduled':
            return (False, "This appointment is not currently scheduled.")
        
        # Check if the appointment is within the allowed time window
        appointment_time = appointment.time
        now = timezone.now()
        
        # Allow joining 15 minutes before and up to 30 minutes after the scheduled time
        time_window_start = appointment_time - timezone.timedelta(minutes=15)
        time_window_end = appointment_time + timezone.timedelta(minutes=30)
        
        if now < time_window_start:
            minutes_until = int((time_window_start - now).total_seconds() / 60)
            return (False, f"You can join this appointment in {minutes_until} minutes.")
        
        if now > time_window_end:
            return (False, "This appointment has ended.")
        
        return (True, "")
    
    @staticmethod
    def get_jitsi_meeting_url(appointment):
        """
        Generate a Jitsi meeting URL for an appointment
        
        Args:
            appointment: Appointment model instance
            
        Returns:
            str: Jitsi meeting URL
        """
        # Generate a unique room name based on the appointment ID
        room_name = f"appointment-{appointment.id}"
        
        # In a real implementation, this might include authentication tokens
        return f"https://meet.jit.si/{room_name}"
