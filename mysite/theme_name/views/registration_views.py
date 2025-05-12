from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db import transaction
from theme_name.forms import PatientRegistrationForm
from patient.models import Patient
from common.utils.ldap_client import LDAPClient
import logging

logger = logging.getLogger(__name__)

def registration_view(request):
    """Main registration view"""
    return render(request, "registration.html")

def prescription_view(request):
    """Prescription request view"""
    if request.method == 'POST':
        form = PrescriptionRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription request submitted successfully!')
            return redirect('prescription_success')
    else:
        form = PrescriptionRequestForm()
    return render(request, "prescription.html", {'form': form})

def login_view(request):
    """Login view"""
    # Placeholder for your actual login implementation
    return render(request, "login.html")

def register_selection(request):
    """View for selecting registration type (patient or provider)"""
    return render(request, "register.html")

def patient_registration(request):
    """Patient registration view with LDAP integration"""
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create User
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name']
                    )
                    
                    # Add to patients group
                    patients_group, _ = Group.objects.get_or_create(name='patients')
                    user.groups.add(patients_group)
                    
                    # Create Patient profile
                    patient = Patient.objects.create(
                        user=user,
                        date_of_birth=form.cleaned_data['date_of_birth'],
                        ohip_number=form.cleaned_data['ohip_number'],
                        primary_phone=form.cleaned_data['primary_phone'],
                        alternate_phone=form.cleaned_data.get('alternate_phone', ''),
                        address=form.cleaned_data['address'],
                        emergency_contact_name=form.cleaned_data['emergency_contact_name'],
                        emergency_contact_phone=form.cleaned_data['emergency_contact_phone'],
                        current_medications=form.cleaned_data.get('current_medications', ''),
                        allergies=form.cleaned_data.get('allergies', ''),
                        pharmacy_details=form.cleaned_data.get('pharmacy_details', ''),
                        virtual_care_consent=form.cleaned_data['virtual_care_consent'],
                        ehr_consent=form.cleaned_data['ehr_consent']
                    )
                    
                    # Create LDAP user
                    ldap_client = LDAPClient()
                    ldap_created = False
                    
                    if ldap_client.connect():
                        try:
                            ldap_data = {
                                'username': user.username,
                                'first_name': user.first_name,
                                'last_name': user.last_name,
                                'email': user.email,
                                'password_hash': ldap_client.generate_password_hash(form.cleaned_data['password'])
                            }
                            
                            if ldap_client.create_user(ldap_data):
                                # Add to patients group in LDAP
                                ldap_client.add_user_to_group(user.username, 'cn=patients,ou=groups,dc=isnord,dc=ca')
                                ldap_created = True
                                logger.info(f"LDAP user created successfully for {user.username}")
                            else:
                                logger.error(f"Failed to create LDAP user for {user.username}")
                                
                        except Exception as e:
                            logger.error(f"LDAP error during user creation: {str(e)}")
                        finally:
                            ldap_client.disconnect()
                    else:
                        logger.error("Failed to connect to LDAP server")
                    
                    # If LDAP creation failed, we might want to warn but still continue
                    if not ldap_created:
                        logger.warning(f"User {user.username} created in Django but not in LDAP")
                        # Optionally, you could raise an exception here to rollback everything
                        # raise Exception("LDAP user creation failed")
                    
                    messages.success(
                        request,
                        'Registration successful! Your account has been created and you can now log in.'
                    )
                    return redirect('registration_success')
                    
            except Exception as e:
                logger.error(f"Error during patient registration: {str(e)}")
                messages.error(
                    request,
                    f'There was an error processing your registration: {str(e)}'
                )
                # The transaction will automatically rollback due to the exception
                
        else:
            # Print form errors for debugging
            logger.debug(f"Form validation errors: {form.errors}")
            
    else:
        form = PatientRegistrationForm()
    
    return render(request, "patient_registration.html", {'form': form})

def provider_registration(request):
    """Provider registration view"""
    if request.method == 'POST':
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            # Save provider registration
            registration = form.save()
            
            messages.success(
                request,
                'Provider registration submitted successfully! Your information has been processed.'
            )
            return redirect('registration_success')
    else:
        form = ProviderRegistrationForm()
    return render(request, "provider_registration.html", {'form': form})

def registration_success(request):
    """Registration success page"""
    return render(request, "registration_success.html")

def schedule_demo(request):
    """Handle demo scheduling requests"""
    if request.method == "POST":
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            try:
                demo_request = form.save()
                
                # Send email notification logic would go here
                # send_mail(...)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Your demo request has been submitted successfully! We will contact you shortly to confirm.'
                })
            except Exception as e:
                print(f"Error saving form: {e}")  # Log the error
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': [f"Server error: {str(e)}"]}
                }, status=500)
        else:
            print(f"Form validation errors: {form.errors}")  # Log validation errors
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    else:
        form = DemoRequestForm()
    
    form_html = render_to_string('partials/demo_form.html', {'form': form})
    return JsonResponse({'form_html': form_html})

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')
