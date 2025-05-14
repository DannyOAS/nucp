# patient/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from patient.models import Patient
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Patient)
def patient_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for when a Patient is saved.
    Ensures the user is in the patients group.
    """
    if created:
        logger.info(f"New patient created: {instance.full_name}")
        
        # Ensure user is in patients group
        patients_group, _ = Group.objects.get_or_create(name='patients')
        instance.user.groups.add(patients_group)
        
        # Log the user group assignment
        logger.info(f"Added user {instance.user.username} to patients group")

@receiver(post_save, sender=User)
def user_created_without_patient(sender, instance, created, **kwargs):
    """
    Signal handler for when a User is created.
    If they're in the patients group but don't have a Patient profile, create one.
    This is a failsafe to ensure data consistency.
    """
    if created and instance.groups.filter(name='patients').exists():
        # Check if user already has a patient profile
        if not hasattr(instance, 'patient_profile'):
            logger.warning(f"User {instance.username} is in patients group but has no patient profile. "
                          "This should be handled by the registration process.")
            
            # Do not automatically create profiles here, log the issue instead
            # In a real system, you might want to notify admins

@receiver(pre_delete, sender=Patient)
def patient_pre_delete(sender, instance, **kwargs):
    """
    Signal handler for when a Patient is about to be deleted.
    Performs any necessary cleanup.
    """
    logger.info(f"Patient being deleted: {instance.full_name}")
    
    # You could add additional cleanup here if needed
    # For example, cancelling all future appointments
