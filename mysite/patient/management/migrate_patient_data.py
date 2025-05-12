# patient/management/commands/migrate_patient_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from patient.models import Patient
from theme_name.repositories import PatientRepository
from common.utils.ldap_client import LDAPClient
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate patient data from repositories to database models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the migration without saving changes',
        )
        parser.add_argument(
            '--create-ldap',
            action='store_true',
            help='Also create LDAP entries for users',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        create_ldap = options['create_ldap']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved'))
        
        # Get patients group
        patients_group, _ = Group.objects.get_or_create(name='patients')
        
        # Get all patients from repository
        repository_patients = PatientRepository.get_all()
        
        success_count = 0
        error_count = 0
        
        for repo_patient in repository_patients:
            try:
                # Check if user already exists
                user = User.objects.filter(email=repo_patient.get('email')).first()
                
                if not user:
                    # Create user
                    username = self._generate_username(repo_patient)
                    
                    if not dry_run:
                        user = User.objects.create_user(
                            username=username,
                            email=repo_patient.get('email'),
                            first_name=repo_patient.get('first_name'),
                            last_name=repo_patient.get('last_name'),
                            password=User.objects.make_random_password()  # Temporary password
                        )
                        user.groups.add(patients_group)
                        
                        self.stdout.write(f"Created user: {username}")
                    else:
                        self.stdout.write(f"Would create user: {username}")
                        user = None
                
                # Check if patient already exists
                if user and hasattr(user, 'patient_profile'):
                    self.stdout.write(f"Patient already exists for user: {user.username}")
                    continue
                
                # Create patient profile
                if user and not dry_run:
                    patient = Patient.objects.create(
                        user=user,
                        date_of_birth=repo_patient.get('date_of_birth'),
                        ohip_number=repo_patient.get('ohip_number'),
                        primary_phone=repo_patient.get('primary_phone'),
                        alternate_phone=repo_patient.get('alternate_phone', ''),
                        address=repo_patient.get('address', ''),
                        emergency_contact_name=repo_patient.get('emergency_contact_name', ''),
                        emergency_contact_phone=repo_patient.get('emergency_contact_phone', ''),
                        current_medications=repo_patient.get('current_medications', ''),
                        allergies=repo_patient.get('allergies', ''),
                        pharmacy_details=repo_patient.get('pharmacy_details', ''),
                        virtual_care_consent=repo_patient.get('virtual_care_consent', False),
                        ehr_consent=repo_patient.get('ehr_consent', False)
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f"Created patient profile for: {user.username}"))
                    
                    # Create LDAP entry if requested
                    if create_ldap:
                        self._create_ldap_user(user, repo_patient)
                    
                    success_count += 1
                else:
                    if dry_run:
                        self.stdout.write(f"Would create patient profile for: {repo_patient.get('email')}")
                        success_count += 1
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"Error processing patient {repo_patient.get('email')}: {str(e)}"))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f"\nMigration complete:"))
        self.stdout.write(f"Successfully processed: {success_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a dry run. No changes were saved."))
    
    def _generate_username(self, patient_data):
        """Generate a unique username for a patient"""
        base_username = f"{patient_data.get('first_name', '').lower()}.{patient_data.get('last_name', '').lower()}"
        base_username = ''.join(c for c in base_username if c.isalnum() or c == '.')
        
        # Ensure uniqueness
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def _create_ldap_user(self, user, patient_data):
        """Create LDAP entry for user"""
        ldap_client = LDAPClient()
        
        if ldap_client.connect():
            try:
                # Generate a temporary password
                temp_password = User.objects.make_random_password()
                
                ldap_data = {
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'password_hash': ldap_client.generate_password_hash(temp_password)
                }
                
                if ldap_client.create_user(ldap_data):
                    # Add to patients group
                    ldap_client.add_user_to_group(user.username, 'cn=patients,ou=groups,dc=isnord,dc=ca')
                    self.stdout.write(f"Created LDAP entry for: {user.username}")
                else:
                    self.stdout.write(self.style.WARNING(f"Failed to create LDAP entry for: {user.username}"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"LDAP error for {user.username}: {str(e)}"))
            finally:
                ldap_client.disconnect()
        else:
            self.stdout.write(self.style.ERROR("Failed to connect to LDAP server"))
