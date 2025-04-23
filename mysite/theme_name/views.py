from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.template.loader import render_to_string
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from .forms import (
    ContactForm, PatientRegistrationForm, ProviderRegistrationForm, PrescriptionRequestForm, 
    PatientForm, PatientProfileEditForm, ProviderProfileEditForm, PatientMessageForm, 
    ProviderMessageForm, DemoRequestForm
)
from .models import PatientRegistration, ContactMessage, BlogPost, Message
from .repositories import (
    PatientRepository, PrescriptionRepository, AppointmentRepository,
    MessageRepository, ProviderRepository
)

from django.utils import timezone
from django.db.models import Q

from datetime import datetime, timedelta, date
from .services import (
    PatientService, PrescriptionService, AppointmentService, 
    MessageService, JitsiService, ProviderService, AIScribeService, 
    FormAutomationService, AIConfigurationService
)
from django.views.decorators.http import require_POST
import json
import logging

logger = logging.getLogger(__name__)

def get_base_context(active_section):
    """
    Create base context with active section.
    Other common data is provided by context processors.
    """
    return {'active_section': active_section}

# ------------------------------
# Main Website Views
# ------------------------------

def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            # Send an email notification
            send_mail(
                subject=f"New Contact Message from {contact_message.name}",
                message=f"Email: {contact_message.email}\n\nMessage:\n{contact_message.message}",
                from_email="your-email@example.com",
                recipient_list=["your-email@example.com"],
                fail_silently=False,
            )
            messages.success(request, "Your message has been sent!")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form})


def registration_view(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # Use service to handle registration
            result = PatientService.register_patient(form.cleaned_data)
            if result['cloud_upload']['success'] and result['erp_sync']['success']:
                messages.success(
                    request,
                    'Registration submitted successfully! Your information has been processed.'
                )
            elif result['cloud_upload']['success']:
                messages.warning(
                    request,
                    'Registration submitted, but failed to sync with ERP system.'
                )
            elif result['erp_sync']['success']:
                messages.warning(
                    request,
                    'Registration submitted, but failed to upload documents to secure storage.'
                )
            else:
                messages.error(
                    request,
                    'Registration submitted locally, but external systems integration failed.'
                )
            return redirect('registration')
    else:
        form = PatientRegistrationForm()
    return render(request, 'registration.html', {'form': form})

########################################################################
#NEW REGISTRATION

def login_view(request):
    """Redirect to Authelia login page"""
    # You can configure this URL to point to your Authelia login endpoint
    authelia_login_url = "https://auth.isnord.ca/auth/"  # Adjust to your actual Authelia URL
    return redirect(authelia_login_url)

def register_selection(request):
    """View for the registration type selection page"""
    return render(request, 'register.html')

def patient_registration(request):
    """View for patient registration form"""
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # Save form data
            result = PatientService.register_patient(form.cleaned_data)
            
            # Success logic (similar to your existing registration_view)
            if result['cloud_upload']['success'] and result['erp_sync']['success']:
                messages.success(
                    request,
                    'Registration submitted successfully! Your information has been processed.'
                )
            elif result['cloud_upload']['success']:
                messages.warning(
                    request,
                    'Registration submitted, but failed to sync with ERP system.'
                )
            elif result['erp_sync']['success']:
                messages.warning(
                    request,
                    'Registration submitted, but failed to upload documents to secure storage.'
                )
            else:
                messages.error(
                    request,
                    'Registration submitted locally, but external systems integration failed.'
                )
                
            return redirect('registration_success')
    else:
        form = PatientRegistrationForm()
    return render(request, 'patient_registration.html', {'form': form})

def provider_registration(request):
    """View for provider registration form"""
    if request.method == 'POST':
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            # Process provider registration
            # Add your provider registration logic here
            messages.success(request, 'Provider registration submitted successfully!')
            return redirect('registration_success')
    else:
        form = ProviderRegistrationForm()  # You'll need to create this form
    return render(request, 'provider_registration.html', {'form': form})

def registration_success(request):
    """View for registration success page"""
    return render(request, 'registration_success.html')


#def schedule_demo(request):
#    if request.method == "POST":
#        form = DemoRequestForm(request.POST)
#        if form.is_valid():
#            demo_request = form.save()
            
            # Send email notification
#            send_mail(
#                subject=f"New Demo Request from {demo_request.name}",
#                message=f"Name: {demo_request.name}\nEmail: {demo_request.email}\nOrganization: {demo_request.organization}\nPhone: {demo_request.phone}\nUser Type: {demo_request.user_type}\nMessage: {demo_request.message}\nPreferred Date: {demo_request.preferred_date}\nPreferred Time: {demo_request.preferred_time}",
#                from_email="notifications@northernhealth.example.com",
#                recipient_list=["sales@northernhealth.example.com"],
#                fail_silently=False,
#            )
            
            # Also send confirmation email to user
#            send_mail(
#                subject="Your Demo Request Confirmation - Northern Health Innovations",
#                message=f"Hello {demo_request.name},\n\nThank you for your interest in NUCP™. We've received your demo request for {demo_request.preferred_date}.\n\nOur team will contact you shortly to confirm the details.\n\nBest regards,\nThe Northern Health Innovations Team",
#                from_email="support@northernhealth.example.com",
#                recipient_list=[demo_request.email],
#                fail_silently=False,
#            )
            
#            return JsonResponse({
#                'success': True,
#                'message': 'Your demo request has been submitted successfully! We will contact you shortly to confirm.'
#            })
#        else:
#            return JsonResponse({
#                'success': False,
#                'errors': form.errors
#            })
#    else:
#        form = DemoRequestForm()
    
#    form_html = render_to_string('partials/demo_form.html', {'form': form})
#    return JsonResponse({'form_html': form_html})

def schedule_demo(request):
    if request.method == "POST":
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            try:
                demo_request = form.save()
                
                # Send email notification (commented out for debugging)
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
#########################################################################

def prescription_view(request):
    if request.method == 'POST':
        form = PrescriptionRequestForm(request.POST)
        if form.is_valid():
            result = PrescriptionService.request_prescription(form.cleaned_data)
            if result['pdf_generated'] and result['cloud_upload']['success']:
                messages.success(request, 'Prescription request submitted successfully!')
            else:
                messages.warning(request, 'Prescription request submitted, but document processing failed.')
            return redirect('prescription')
    else:
        form = PrescriptionRequestForm()
    return render(request, 'prescription.html', {'form': form})


def blog_list(request):
    posts = BlogPost.objects.all().order_by("-created_at")
    return render(request, "blog_list.html", {"posts": posts})


def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    return render(request, "blog_detail.html", {"post": post})
# ------------------------------
# Patient Dashboard Views
# ------------------------------

def logout_view(request):
    """Log out the user and redirect to home page."""
    logout(request)
    return redirect('home')  # Replace with your home page URL name


#def patient_dashboard(request):
#    patient = PatientRepository.get_current(request)
#    dashboard_data = PatientService.get_dashboard_data(patient['id'])
#    context = {**dashboard_data, **get_base_context('dashboard')}
#    return render(request, "patient/dashboard.html", context)

def patient_dashboard(request):
    patient = PatientRepository.get_current(request)
    dashboard_data = PatientService.get_dashboard_data(patient['id'])
    
    # Add messaging data for the dashboard
    unread_messages_count = 0
    recent_messages = []
    
    if request.user.is_authenticated:
        # Get unread message count
        unread_messages_count = Message.objects.filter(
            recipient=request.user, 
            status='unread'
        ).count()
        
        # Get recent messages (limit to 2 for dashboard)
        recent_messages = Message.objects.filter(
            recipient=request.user
        ).exclude(
            status='deleted'
        ).order_by('-created_at')[:2]
    
    # Add message data to context
    dashboard_data['unread_messages_count'] = unread_messages_count
    dashboard_data['recent_messages'] = recent_messages
    
    context = {**dashboard_data, **get_base_context('dashboard')}
    return render(request, "patient/dashboard.html", context)

# views.py - Update the patient_profile view
def patient_profile(request):
    """Patient profile page with edit functionality"""
    patient = PatientRepository.get_current(request)
    
    if request.method == 'POST':
        form = PatientProfileEditForm(request.POST)
        if form.is_valid():
            # Get cleaned data from form
            updated_data = form.cleaned_data
            
            # Update patient data via repository
            PatientRepository.update(patient['id'], updated_data)
            
            # Get updated patient data
            patient = PatientRepository.get_by_id(patient['id'])
            
            # Add success message
            messages.success(request, "Profile updated successfully!")
            
            # Redirect to profile page to prevent form resubmission
            return redirect('patient_profile')
    else:
        # Pre-fill form with existing patient data
        form = PatientProfileEditForm(initial={
            'first_name': patient.get('first_name', ''),
            'last_name': patient.get('last_name', ''),
            'email': patient.get('email', ''),
            'primary_phone': patient.get('primary_phone', ''),
            'alternate_phone': patient.get('alternate_phone', ''),
            'address': patient.get('address', ''),
            'emergency_contact_name': patient.get('emergency_contact_name', ''),
            'emergency_contact_phone': patient.get('emergency_contact_phone', '')
        })
    
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_section': 'profile',
        'form': form
    }
    return render(request, "patient/profile.html", context)

def patient_medical_history(request):
    """Patient medical history page"""
    patient = PatientRepository.get_current(request)
    # In a real app, you'd fetch actual medical history here
    medical_history = [
        {'date': 'March 15, 2025', 'provider': 'Dr. Johnson', 'description': 'Annual checkup', 'notes': 'All vitals normal'},
        {'date': 'January 10, 2025', 'provider': 'Dr. Smith', 'description': 'Flu symptoms', 'notes': 'Prescribed rest and fluids'},
        {'date': 'November 5, 2024', 'provider': 'Dr. Wilson', 'description': 'Vaccination', 'notes': 'COVID-19 booster administered'}
    ]
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_section': 'medical_history',
        'medical_history': medical_history
    }
    return render(request, "patient/medical_history.html", context)

def patient_help_center(request):
    """Patient help center page"""
    patient = PatientRepository.get_current(request)
    context = {
        'patient': patient,
        'patient_name': f"{patient['first_name']} {patient['last_name']}",
        'active_section': 'help_center'
    }
    return render(request, "patient/help_center.html", context)

def patient_prescriptions(request):
    patient = PatientRepository.get_current(request)
    prescription_data = PrescriptionService.get_prescriptions_dashboard(patient['id'])
    context = {
        **prescription_data,
        'pharmacy': {
            'name': 'Northern Pharmacy',
            'address': '123 Health Street',
            'city_state_zip': 'Anytown, ST 12345',
            'phone': '(555) 123-4567'
        },
        **get_base_context('prescriptions')
    }
    return render(request, "patient/prescriptions.html", context)


def patient_search(request):
    patient = PatientRepository.get_current(request)
    search_query = request.GET.get('query', '')
    results = {}
    if search_query:
        results = PatientService.search_patient_records(patient['id'], search_query)
    context = {
        'query': search_query,
        'results': results,
        'active_section': 'search',
        'patient_name': f"{patient['first_name']} {patient['last_name']}"
    }
    return render(request, "patient/search_results.html", context)


def appointments_view(request):
    patient = PatientRepository.get_current(request)
    appointment_data = AppointmentService.get_appointments_dashboard(patient['id'])
    context = {**appointment_data, **get_base_context('appointments')}
    return render(request, "patient/appointments.html", context)


def email_view(request):
    patient = PatientRepository.get_current(request)
    message_data = MessageService.get_message_dashboard(patient['id'])
    context = {**message_data, **get_base_context('email')}
    return render(request, "patient/email.html", context)

#def messages_view(request):
#    patient = PatientRepository.get_current(request)
#    message_data = MessageService.get_message_dashboard(patient['id'])
#    context = {**message_data, **get_base_context('messages')}
#    return render(request, "patient/messages.html", context)

#@login_required
def patient_messages(request):
    """View for patients to see their messages"""
    # Get counts for inbox stats
    unread_count = Message.objects.filter(recipient=request.user, status='unread').count()
    read_count = Message.objects.filter(recipient=request.user, status='read').count()
    sent_count = Message.objects.filter(sender=request.user).exclude(status='deleted').count()
    archived_count = Message.objects.filter(recipient=request.user, status='archived').count()
    
    # Get messages
    unread_messages = Message.objects.filter(recipient=request.user, status='unread')
    read_messages = Message.objects.filter(recipient=request.user, status='read')
    
    # Combined queryset for pagination
    all_messages = unread_messages.union(read_messages).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(all_messages, 10)  # Show 10 messages per page
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    # Split the page results back into unread and read for display
    page_unread = [msg for msg in messages_page if msg.status == 'unread']
    page_read = [msg for msg in messages_page if msg.status == 'read']
    
    context = {
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'archived_count': archived_count,
        'unread_messages': page_unread,
        'read_messages': page_read,
        'page_obj': messages_page,
        'active_section': 'email'  # For highlighting in sidebar
    }
    
    return render(request, 'patient/patient_messages.html', context)

#@login_required
def patient_sent_messages(request):
    """View for patients to see messages they've sent"""
    # Get sent messages
    sent_messages = Message.objects.filter(sender=request.user).exclude(status='deleted')
    
    # Pagination
    paginator = Paginator(sent_messages, 10)
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    context = {
        'sent_messages': messages_page,
        'page_obj': messages_page,
        'folder': 'sent',
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_sent_messages.html', context)

#@login_required
def patient_archived_messages(request):
    """View for patients to see archived messages"""
    # Get archived messages
    archived_messages = Message.objects.filter(recipient=request.user, status='archived')
    
    # Pagination
    paginator = Paginator(archived_messages, 10)
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    context = {
        'archived_messages': messages_page,
        'page_obj': messages_page,
        'folder': 'archived',
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_archived_messages.html', context)

#@login_required
def patient_view_message(request, message_id):
    """View for patients to read a specific message"""
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    # Mark as read if unread
    if message.status == 'unread':
        message.mark_as_read()
    
    context = {
        'message': message,
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_view_message.html', context)

#@login_required
def patient_compose_message(request):
    """View for patients to compose a new message"""
    if request.method == 'POST':
        form = PatientMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            
            # Determine the recipient based on recipient_type
            recipient_type = form.cleaned_data['recipient_type']
            
            # In a real implementation, we would have a mapping to actual users
            # For now, we'll use a placeholder approach
            from django.contrib.auth.models import User
            
            if recipient_type == 'provider':
                # Assign to the patient's provider
                # For mock implementation, just get the first staff user
                provider = User.objects.filter(is_staff=True).first()
                if provider:
                    message.recipient = provider
                else:
                    messages.error(request, "No provider found in the system.")
                    return redirect('patient_messages')
            elif recipient_type == 'pharmacy':
                # Assign to pharmacy user
                pharmacy_user = User.objects.filter(username='pharmacy').first()
                if pharmacy_user:
                    message.recipient = pharmacy_user
                else:
                    messages.error(request, "Pharmacy service not available.")
                    return redirect('patient_messages')
            elif recipient_type == 'billing':
                # Assign to billing department
                billing_user = User.objects.filter(username='billing').first()
                if billing_user:
                    message.recipient = billing_user
                else:
                    messages.error(request, "Billing department not available.")
                    return redirect('patient_messages')
            
            message.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('patient_messages')
    else:
        form = PatientMessageForm()
    
    context = {
        'form': form,
        'active_section': 'email'
    }
    
    return render(request, 'patient/patient_compose_message.html', context)

#@login_required
def patient_message_action(request, message_id, action):
    """Handle message actions (mark read/unread, archive, delete)"""
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    if action == 'mark_read':
        message.mark_as_read()
        messages.success(request, "Message marked as read.")
    elif action == 'mark_unread':
        message.mark_as_unread()
        messages.success(request, "Message marked as unread.")
    elif action == 'archive':
        message.archive()
        messages.success(request, "Message archived.")
    elif action == 'delete':
        message.delete_message()
        messages.success(request, "Message deleted.")
    
    # Redirect based on the current folder
    referer = request.META.get('HTTP_REFERER', '')
    if 'archived' in referer:
        return redirect('patient_archived_messages')
    elif 'sent' in referer:
        return redirect('patient_sent_messages')
    else:
        return redirect('patient_messages')


##################################################################################
def jitsi_video_view(request):
    patient = PatientRepository.get_current(request)
    video_data = JitsiService.get_video_dashboard(patient['id'])
    context = {**video_data, **get_base_context('video')}
    return render(request, "patient/jitsi.html", context)


def request_prescription(request):
    patient = PatientRepository.get_current(request)
    if request.method == 'POST':
        form = PrescriptionRequestForm(request.POST)
        if form.is_valid():
            result = PrescriptionService.request_prescription(form.cleaned_data)
            if result['cloud_upload']['success']:
                messages.success(request, 'Prescription request submitted successfully!')
            else:
                messages.warning(request, 'Prescription request submitted, but PDF upload failed.')
            return redirect('patient_prescriptions')
    else:
        initial_data = {
            'first_name': patient['first_name'],
            'last_name': patient['last_name'],
            'date_of_birth': patient['date_of_birth'],
            'ohip_number': patient['ohip_number'],
            'phone_number': patient['primary_phone']
        }
        form = PrescriptionRequestForm(initial=initial_data)
    context = {'form': form, **get_base_context('prescriptions')}
    return render(request, "patient/request_prescription.html", context)


def request_refill(request, prescription_id):
    prescription = PrescriptionRepository.get_by_id(prescription_id)
    if not prescription:
        raise Http404("Prescription not found")
    patient = PatientRepository.get_current(request)
    if request.method == 'POST':
        refill_data = {
            'pharmacy': request.POST.get('pharmacy'),
            'other_pharmacy_name': request.POST.get('other_pharmacy_name'),
            'other_pharmacy_address': request.POST.get('other_pharmacy_address'),
            'other_pharmacy_phone': request.POST.get('other_pharmacy_phone'),
            'last_dose_taken': request.POST.get('last_dose_taken'),
            'medication_changes': request.POST.get('medication_changes'),
            'changes_description': request.POST.get('changes_description'),
            'side_effects': request.POST.get('side_effects'),
            'notes': request.POST.get('notes'),
            'information_consent': request.POST.get('information_consent') == 'on',
            'pharmacy_consent': request.POST.get('pharmacy_consent') == 'on'
        }
        result = PrescriptionService.request_refill(prescription_id, refill_data)
        if result['success']:
            messages.success(request, f"Refill request for {prescription['medication_name']} submitted successfully!")
        else:
            messages.error(request, f"Error processing refill request: {result.get('error', 'Unknown error')}")
        return redirect('patient_prescriptions')
    context = {'prescription': prescription, **get_base_context('prescriptions')}
    return render(request, "patient/request_refill.html", context)


def prescription_detail(request, prescription_id):
    prescription = PrescriptionRepository.get_by_id(prescription_id)
    if not prescription:
        raise Http404("Prescription not found")
    context = {'prescription': prescription, **get_base_context('prescriptions')}
    return render(request, "patient/prescription_detail.html", context)


# ------------------------------
# Provider Dashboard Views
# ------------------------------

def provider_dashboard(request):
    provider_id = 1  # In production, replace with request.user
    dashboard_data = ProviderService.get_dashboard_data(provider_id)
    context = {**dashboard_data, 'active_section': 'dashboard', 'today': datetime.now().date()}
    return render(request, "provider/dashboard.html", context)

# views.py - Update the provider_profile view
def provider_profile(request):
    """Provider profile page with edit functionality"""
    provider_id = 1  # In production, replace with request.user.id
    provider = ProviderRepository.get_by_id(provider_id)
    
    if request.method == 'POST':
        form = ProviderProfileEditForm(request.POST)
        if form.is_valid():
            # Get cleaned data from form
            updated_data = form.cleaned_data
            
            # Update provider data via repository
            ProviderRepository.update(provider_id, updated_data)
            
            # Get updated provider data
            provider = ProviderRepository.get_by_id(provider_id)
            
            # Add success message
            messages.success(request, "Profile updated successfully!")
            
            # Redirect to profile page to prevent form resubmission
            return redirect('provider_profile')
    else:
        # Pre-fill form with existing provider data
        form = ProviderProfileEditForm(initial={
            'first_name': provider.get('first_name', ''),
            'last_name': provider.get('last_name', ''),
            'email': provider.get('email', ''),
            'phone': provider.get('phone', ''),
            'specialty': provider.get('specialty', ''),
            'bio': provider.get('bio', '')
        })
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'profile',
        'form': form
    }
    return render(request, "provider/profile.html", context)

def provider_settings(request):
    """Provider settings page"""
    provider_id = 1  # In production, replace with request.user.id
    provider = ProviderRepository.get_by_id(provider_id)
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'settings'
    }
    return render(request, "provider/settings.html", context)

def provider_help_support(request):
    """Provider help and support page"""
    provider_id = 1  # In production, replace with request.user.id
    provider = ProviderRepository.get_by_id(provider_id)
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'active_section': 'help_support'
    }
    return render(request, "provider/help_support.html", context)

def provider_patients(request):
    provider_id = 1  # In production, replace with request.user.id
    
    # Get search query if present
    search_query = request.GET.get('search', '')
    
    # Get filter parameter if present (all, recent, upcoming, attention)
    filter_type = request.GET.get('filter', 'all')
    
    # Get provider patients
    patients = ProviderRepository.get_patients(provider_id)
    
    # Apply search filter if search query exists
    if search_query:
        patients = [
            p for p in patients 
            if search_query.lower() in p.get('first_name', '').lower() or 
               search_query.lower() in p.get('last_name', '').lower() or
               search_query.lower() in p.get('email', '').lower() or
               search_query.lower() in p.get('ohip_number', '').lower()
        ]
    
    # Apply additional filters based on filter_type
    if filter_type == 'recent':
        # Filter patients with recent activity (last 7 days)
        # This is a simplification - in a real app you'd check last_visit dates
        patients = [p for p in patients if p.get('last_visit', '') != '']
    elif filter_type == 'upcoming':
        # Filter patients with upcoming appointments
        patients = [p for p in patients if p.get('upcoming_appointment', '') != '']
    elif filter_type == 'attention':
        # Filter patients requiring attention
        # This could be based on various criteria - here we're using a simplification
        patients = [p for p in patients if 'requires_attention' in p and p['requires_attention']]
    
    # Handle pagination
    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(patients, items_per_page)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get recent patient activity
    recent_activity = ProviderService.get_recent_patient_activity(provider_id)
    
    # Calculate stats
    total_patients = len(ProviderRepository.get_patients(provider_id))
    appointments_this_week = len([p for p in patients if p.get('upcoming_appointment', '') != ''])
    requiring_attention = len([p for p in patients if 'requires_attention' in p and p['requires_attention']])
    
    context = {
        'patients': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'stats': {
            'total_patients': total_patients,
            'appointments_this_week': appointments_this_week,
            'requiring_attention': requiring_attention
        },
        'recent_activity': recent_activity[:5],  # Limit to 5 most recent activities
        'active_section': 'patients',
        'provider_name': 'Dr. Smith'  # Replace with actual provider name in production
    }
    
    return render(request, 'provider/patients.html', context)

def add_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            # Use the PatientService to register the patient
            # Change from_provider to False so it performs the Nextcloud upload
            result = PatientService.register_patient(form.cleaned_data, request, from_provider=True)
            
            # Check if the upload to Nextcloud was successful
            if result.get('patient'):
                if result.get('cloud_upload', {}).get('success'):
                    messages.success(request, f"Patient {form.cleaned_data['first_name']} {form.cleaned_data['last_name']} was added successfully and documents were uploaded to Nextcloud.")
                else:
                    messages.warning(request, f"Patient {form.cleaned_data['first_name']} {form.cleaned_data['last_name']} was added successfully, but there was an issue uploading to Nextcloud.")
                
                return redirect('provider_patients')
            else:
                messages.error(request, "There was an error adding the patient.")
    else:
        form = PatientForm()
    
    context = {
        'form': form,
        'active_section': 'patients',
        'provider_name': 'Dr. Smith'  # Replace with actual provider name in production
    }
    return render(request, 'provider/add_patient.html', context)

def view_patient(request, patient_id):
    print(f"[VIEW] Viewing patient_id: {patient_id}, type: {type(patient_id)}")
    # Get the patient from the repository
    patient = PatientRepository.get_by_id(patient_id)
    
    print(f"[VIEW] Retrieved patient: {patient.get('first_name')} {patient.get('last_name')}, ID: {patient.get('id')}")

    if not patient:
        messages.error(request, f"Patient with ID {patient_id} not found.")
        return redirect('provider_patients')

    # Convert patient_id to integer if it's a string
    if isinstance(patient_id, str) and patient_id.isdigit():
        patient_id = int(patient_id)

    # Get related patient data
    appointments = AppointmentRepository.get_upcoming_for_patient(patient_id)
    past_appointments = AppointmentRepository.get_past_for_patient(patient_id)
    prescriptions = PrescriptionRepository.get_active_for_patient(patient_id)
    historical_prescriptions = PrescriptionRepository.get_historical_for_patient(patient_id)
    
    # Format the patient name
    patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
    
    context = {
        'patient': patient,
        'patient_name': patient_name,
        'appointments': appointments,
        'past_appointments': past_appointments,
        'prescriptions': prescriptions,
        'historical_prescriptions': historical_prescriptions,
        'active_section': 'patients',
        'provider_name': 'Dr. Smith'  # Replace with actual provider name in production
    }
    
    return render(request, 'provider/view_patient.html', context)

def provider_appointments(request):
    provider_id = 1
    appointments_data = ProviderService.get_appointments_dashboard(provider_id)
    context = {**appointments_data, 'active_section': 'appointments', 'provider_name': 'Dr. Smith'}
    return render(request, 'provider/appointments.html', context)


def provider_prescriptions(request):
    from django.conf import settings
    from .data_access import get_provider_prescription_requests

    provider_id = 1  # Replace with request.user for production
    # Direct data access test (for debugging)
    direct_data = get_provider_prescription_requests(provider_id)
    print("DEBUG - Direct data access call result:", direct_data)

    time_period = request.GET.get('period', 'week')
    search_query = request.GET.get('search', '')
    try:
        prescriptions_data = ProviderService.get_prescriptions_dashboard(
            provider_id,
            time_period=time_period,
            search_query=search_query
        )
        print("DEBUG - Service call successful")
    except Exception as e:
        print(f"DEBUG - Exception in service call: {e}")
        prescriptions_data = {
            'stats': {'active_prescriptions': 0, 'pending_renewals': 0, 'new_today': 0, 'refill_requests': 0},
            'prescription_requests': [],
            'recent_prescriptions': []
        }
    print("DEBUG - Full prescriptions_data:", prescriptions_data)

    page_number = request.GET.get('page', 1)
    items_per_page = 10
    paginator = Paginator(prescriptions_data.get('recent_prescriptions', []), items_per_page)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    today = datetime.now().date()
    for req in prescriptions_data.get('prescription_requests', []):
        req['expiration_date'] = req.get('expires', 'N/A')
        req['days_left'] = None
        if 'expires' in req:
            try:
                expiration_date = None
                if isinstance(req['expires'], str):
                    formats = ['%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']
                    for fmt in formats:
                        try:
                            expiration_date = datetime.strptime(req['expires'], fmt).date()
                            break
                        except ValueError:
                            continue
                elif isinstance(req['expires'], datetime):
                    expiration_date = req['expires'].date()
                elif isinstance(req['expires'], date):
                    expiration_date = req['expires']
                if expiration_date:
                    req['days_left'] = max(0, (expiration_date - today).days)
            except Exception as e:
                logger.warning(f"Error calculating expiration for {req.get('medication_name')}: {e}")

    context = {
        'stats': prescriptions_data.get('stats', {}),
        'prescription_requests': prescriptions_data.get('prescription_requests', []),
        'recent_prescriptions': page_obj,
        'active_section': 'prescriptions',
        'provider_name': 'Dr. Smith',
        'time_period': time_period,
        'search_query': search_query,
        'page_obj': page_obj
    }
    return render(request, 'provider/prescriptions.html', context)


def approve_prescription(request, prescription_id):
    try:
        success = PrescriptionRepository.approve_prescription(prescription_id)
        if success:
            messages.success(request, "Prescription renewal approved successfully.")
        else:
            messages.error(request, "Error approving prescription renewal.")
    except Exception as e:
        logger.error(f"Error approving prescription: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
    return redirect('provider_prescriptions')


def review_prescription(request, prescription_id):
    try:
        prescription = PrescriptionRepository.get_by_id(prescription_id)
        if not prescription:
            messages.error(request, f"Prescription with ID {prescription_id} not found.")
            return redirect('provider_prescriptions')
        patient = PatientRepository.get_by_id(prescription.get('patient_id')) if prescription.get('patient_id') else None
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'approve':
                success = PrescriptionRepository.approve_prescription(prescription_id)
                if success:
                    messages.success(request, "Prescription renewal approved successfully.")
                    return redirect('provider_prescriptions')
                else:
                    messages.error(request, "Error approving prescription renewal.")
            elif action == 'deny':
                notes = request.POST.get('denial_notes', '')
                updated_data = {
                    'status': 'Denied',
                    'denial_notes': notes,
                    'denial_date': datetime.now().isoformat()
                }
                updated = PrescriptionRepository.update(prescription_id, updated_data)
                if updated:
                    messages.success(request, "Prescription renewal denied.")
                    return redirect('provider_prescriptions')
                else:
                    messages.error(request, "Error denying prescription renewal.")
            elif action == 'modify':
                modified_data = {
                    'dosage': request.POST.get('dosage'),
                    'refills_remaining': request.POST.get('refills'),
                    'instructions': request.POST.get('instructions'),
                    'notes': request.POST.get('notes')
                }
                updated = PrescriptionRepository.update(prescription_id, modified_data)
                if updated:
                    messages.success(request, "Prescription updated successfully.")
                    return redirect('provider_prescriptions')
                else:
                    messages.error(request, "Error updating prescription.")
        context = {
            'prescription': prescription,
            'patient': patient,
            'active_section': 'prescriptions',
            'provider_name': 'Dr. Smith'
        }
        return render(request, 'provider/review_prescription.html', context)
    except Exception as e:
        logger.error(f"Error reviewing prescription: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('provider_prescriptions')


def create_prescription(request):
    try:
        if request.method == 'POST':
            prescription_data = {
                'medication_name': request.POST.get('medication_name'),
                'dosage': request.POST.get('dosage'),
                'prescribed_by': f"Dr. {request.POST.get('prescribed_by', 'Provider')}",
                'prescribed_date': datetime.now().strftime('%B %d, %Y'),
                'refills_remaining': int(request.POST.get('refills', 0)),
                'status': 'Active',
                'instructions': request.POST.get('instructions'),
                'side_effects': request.POST.get('side_effects'),
                'warnings': request.POST.get('warnings'),
                'expires': (datetime.now() + timedelta(days=30 * int(request.POST.get('duration_months', 1)))).strftime('%B %d, %Y'),
                'pharmacy': request.POST.get('pharmacy')
            }
            patient_id = request.POST.get('patient_id')
            if patient_id:
                patient = PatientRepository.get_by_id(patient_id)
                if patient:
                    prescription_data['patient_id'] = patient_id
                    prescription_data['patient_name'] = f"{patient.get('first_name')} {patient.get('last_name')}"
            created = PrescriptionRepository.create(prescription_data)
            if created:
                messages.success(
                    request,
                    f"Prescription for {prescription_data['medication_name']} created successfully."
                )
                return redirect('provider_prescriptions')
            else:
                messages.error(request, "Error creating prescription.")
        patients = PatientRepository.get_all()
        context = {
            'patients': patients,
            'active_section': 'prescriptions',
            'provider_name': 'Dr. Smith'
        }
        return render(request, 'provider/create_prescription.html', context)
    except Exception as e:
        logger.error(f"Error creating prescription: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('provider_prescriptions')


def edit_prescription(request, prescription_id):
    try:
        prescription = PrescriptionRepository.get_by_id(prescription_id)
        if not prescription:
            messages.error(request, f"Prescription with ID {prescription_id} not found.")
            return redirect('provider_prescriptions')
        if request.method == 'POST':
            prescription_data = {
                'medication_name': request.POST.get('medication_name'),
                'dosage': request.POST.get('dosage'),
                'refills_remaining': int(request.POST.get('refills', 0)),
                'status': request.POST.get('status', prescription.get('status')),
                'instructions': request.POST.get('instructions'),
                'side_effects': request.POST.get('side_effects'),
                'warnings': request.POST.get('warnings'),
                'pharmacy': request.POST.get('pharmacy')
            }
            if 'duration_months' in request.POST:
                try:
                    prescribed_date = datetime.strptime(
                        prescription.get('prescribed_date', datetime.now().strftime('%B %d, %Y')),
                        '%B %d, %Y'
                    )
                    new_expiration = prescribed_date + timedelta(days=30 * int(request.POST.get('duration_months', 1)))
                    prescription_data['expires'] = new_expiration.strftime('%B %d, %Y')
                except (ValueError, TypeError):
                    new_expiration = datetime.now() + timedelta(days=30 * int(request.POST.get('duration_months', 1)))
                    prescription_data['expires'] = new_expiration.strftime('%B %d, %Y')
            updated = PrescriptionRepository.update(prescription_id, prescription_data)
            if updated:
                messages.success(
                    request,
                    f"Prescription for {prescription_data['medication_name']} updated successfully."
                )
                return redirect('provider_prescriptions')
            else:
                messages.error(request, "Error updating prescription.")
        patient = None
        patient_id = prescription.get('patient_id')
        if patient_id:
            patient = PatientRepository.get_by_id(patient_id)
        context = {
            'prescription': prescription,
            'patient': patient,
            'active_section': 'prescriptions',
            'provider_name': 'Dr. Smith'
        }
        return render(request, 'provider/edit_prescription.html', context)
    except Exception as e:
        logger.error(f"Error editing prescription: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('provider_prescriptions')


def provider_messages(request):
    provider_id = 1
    messages_data = ProviderService.get_messages_dashboard(provider_id)
    context = {**messages_data, 'active_section': 'messages', 'provider_name': 'Dr. Smith'}
    return render(request, 'provider/messages.html', context)
###########################################
# Provider Messaging Views
#@login_required
def provider_messages(request):
    """View for providers to see their messages"""
    # Check if user is a provider (staff user)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get counts for inbox stats
    unread_count = Message.objects.filter(recipient=request.user, status='unread').count()
    read_count = Message.objects.filter(recipient=request.user, status='read').count()
    sent_count = Message.objects.filter(sender=request.user).exclude(status='deleted').count()
    archived_count = Message.objects.filter(recipient=request.user, status='archived').count()
    
    # Get messages
    unread_messages = Message.objects.filter(recipient=request.user, status='unread')
    read_messages = Message.objects.filter(recipient=request.user, status='read')
    
    # Combined queryset for pagination
    all_messages = unread_messages.union(read_messages).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(all_messages, 10)
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    # Split the page results back into unread and read for display
    page_unread = [msg for msg in messages_page if msg.status == 'unread']
    page_read = [msg for msg in messages_page if msg.status == 'read']
    
    context = {
        'unread_count': unread_count,
        'read_count': read_count,
        'sent_count': sent_count,
        'archived_count': archived_count,
        'unread_messages': page_unread,
        'read_messages': page_read,
        'page_obj': messages_page,
        'active_section': 'messages'  # For highlighting in sidebar
    }
    
    return render(request, 'provider/provider_messages.html', context)

#@login_required
def provider_sent_messages(request):
    """View for providers to see messages they've sent"""
    # Check if user is a provider (staff user)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get sent messages
    sent_messages = Message.objects.filter(sender=request.user).exclude(status='deleted')
    
    # Pagination
    paginator = Paginator(sent_messages, 10)
    page = request.GET.get('page')
    
    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)
    
    context = {
        'sent_messages': messages_page,
        'page_obj': messages_page,
        'folder': 'sent',
        'active_section': 'messages'
    }
    
    return render(request, 'provider/provider_sent_messages.html', context)

#@login_required
def provider_view_message(request, message_id):
    """View for providers to read a specific message"""
    # Check if user is a provider (staff user)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    # Mark as read if unread
    if message.status == 'unread':
        message.mark_as_read()
    
    context = {
        'message': message,
        'active_section': 'messages'
    }
    
    return render(request, 'provider/provider_view_message.html', context)

#@login_required
def provider_compose_message(request):
    """View for providers to compose a new message"""
    # Check if user is a provider (staff user)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ProviderMessageForm(request.POST, provider=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient_type = 'patient'  # Since provider is sending to patient
            message.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('provider_messages')
    else:
        form = ProviderMessageForm(provider=request.user)
    
    context = {
        'form': form,
        'active_section': 'messages'
    }
    
    return render(request, 'provider/provider_compose_message.html', context)

#@login_required
def provider_message_action(request, message_id, action):
    """Handle message actions (mark read/unread, archive, delete)"""
    # Check if user is a provider (staff user)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    if action == 'mark_read':
        message.mark_as_read()
        messages.success(request, "Message marked as read.")
    elif action == 'mark_unread':
        message.mark_as_unread()
        messages.success(request, "Message marked as unread.")
    elif action == 'archive':
        message.archive()
        messages.success(request, "Message archived.")
    elif action == 'delete':
        message.delete_message()
        messages.success(request, "Message deleted.")
    
    # Redirect based on the current folder
    referer = request.META.get('HTTP_REFERER', '')
    if 'archived' in referer:
        return redirect('provider_archived_messages')
    elif 'sent' in referer:
        return redirect('provider_sent_messages')
    else:
        return redirect('provider_messages')

####################################

def provider_video_consultation(request):
    provider_id = 1
    from .data_access import get_provider_appointments
    all_appointments = get_provider_appointments(provider_id)
    video_appointments = [a for a in all_appointments if a.get('type') == 'Virtual']
    context = {
        'active_section': 'consultations',
        'provider_name': 'Dr. Provider',
        'video_appointments': video_appointments
    }
    return render(request, 'provider/video_consultation.html', context)
# ------------------------------
# Admin Dashboard Views
# ------------------------------

def admin_dashboard(request):
    from .data_access import get_current_admin, get_system_stats, get_admin_logs
    admin = get_current_admin(request)
    stats = get_system_stats()
    logs = get_admin_logs(limit=10)
    return render(request, "admin/dashboard.html", {
        'admin': admin,
        'stats': stats,
        'logs': logs
    })


def admin_patients(request):
    from .data_access import get_all_patients
    patients = get_all_patients()
    search_query = request.GET.get('search', '')
    if search_query:
        patients = [
            p for p in patients 
            if search_query.lower() in p['first_name'].lower() or 
               search_query.lower() in p['last_name'].lower() or
               search_query.lower() in p['email'].lower()
        ]
    return render(request, 'admin_patients.html', {'patients': patients})


def admin_providers(request):
    from .data_access import get_all_providers
    providers = get_all_providers()
    search_query = request.GET.get('search', '')
    if search_query:
        providers = [
            p for p in providers 
            if search_query.lower() in p['first_name'].lower() or 
               search_query.lower() in p['last_name'].lower() or
               search_query.lower() in p['email'].lower()
        ]
    return render(request, 'admin_providers.html', {'providers': providers})


def admin_logs(request):
    from .data_access import get_admin_logs
    logs = get_admin_logs()
    log_type = request.GET.get('type', '')
    if log_type:
        logs = [log for log in logs if log['action'] == log_type]
    return render(request, 'admin_logs.html', {'logs': logs})


# ------------------------------
# AI Configuration and Scribe Views
# ------------------------------

def ai_config_dashboard(request):
    try:
        status_result = AIConfigurationService.get_system_status()
        configs_result = AIConfigurationService.get_active_model_configs()
        context = {
            'active_section': 'ai_config',
            'admin_name': 'Administrator',
            'system_status': status_result if status_result.get('success') else {'error': 'System status unavailable'},
            'model_configs': configs_result.get('configs', [])
        }
        return render(request, "admin/ai_dashboard.html", context)
    except Exception as e:
        logger.error(f"Error in ai_config_dashboard view: {str(e)}")
        context = {
            'active_section': 'ai_config',
            'admin_name': 'Administrator',
            'error_message': f"An error occurred: {str(e)}"
        }
        return render(request, "admin/ai_dashboard.html", context)


def edit_model_config(request, config_id):
    configs_result = AIConfigurationService.get_active_model_configs()
    if not configs_result.get('success'):
        messages.error(request, f"Error loading model configurations: {configs_result.get('error', 'Unknown error')}")
        return redirect('ai_config_dashboard')
    config = next((c for c in configs_result.get('configs', []) if c['id'] == config_id), None)
    if not config:
        messages.error(request, f"Configuration not found with ID: {config_id}")
        return redirect('ai_config_dashboard')
    if request.method == 'POST':
        config_data = request.POST.dict()
        update_result = AIConfigurationService.update_model_config(config_id, config_data)
        if update_result.get('success'):
            messages.success(request, "Configuration updated successfully!")
            return redirect('ai_config_dashboard')
        else:
            messages.error(request, f"Error updating configuration: {update_result.get('error', 'Unknown error')}")
    context = {
        'active_section': 'ai_config',
        'admin_name': 'Administrator',
        'config': config
    }
    return render(request, 'edit_model_config.html', context)


def templates_dashboard(request):
    templates_result = FormAutomationService.get_available_templates()
    context = {
        'active_section': 'templates',
        'admin_name': 'Administrator',
        'templates': templates_result.get('templates', [])
    }
    return render(request, 'templates_dashboard.html', context)


def create_template(request):
    if request.method == 'POST':
        template_data = request.POST.dict()
        # Create the template in the database (implementation needed)
        messages.success(request, "Template created successfully!")
        return redirect('templates_dashboard')
    context = {
        'active_section': 'templates',
        'admin_name': 'Administrator',
        'template_types': [
            {'value': 'lab_req', 'label': 'Lab Requisition'},
            {'value': 'sick_note', 'label': 'Sick Note'},
            {'value': 'referral', 'label': 'Referral Letter'},
            {'value': 'insurance', 'label': 'Insurance Form'},
            {'value': 'prescription', 'label': 'Prescription Form'},
            {'value': 'other', 'label': 'Other'}
        ]
    }
    return render(request, 'admin/create_template.html', context)


def edit_template(request, template_id):
    template_result = FormAutomationService.get_template_by_id(template_id)
    if not template_result.get('success'):
        messages.error(request, f"Error loading template: {template_result.get('error', 'Unknown error')}")
        return redirect('templates_dashboard')
    if request.method == 'POST':
        template_data = request.POST.dict()
        # Update the template in the database (implementation needed)
        messages.success(request, "Template updated successfully!")
        return redirect('templates_dashboard')
    context = {
        'active_section': 'templates',
        'admin_name': 'Administrator',
        'template': template_result.get('template'),
        'template_types': [
            {'value': 'lab_req', 'label': 'Lab Requisition'},
            {'value': 'sick_note', 'label': 'Sick Note'},
            {'value': 'referral', 'label': 'Referral Letter'},
            {'value': 'insurance', 'label': 'Insurance Form'},
            {'value': 'prescription', 'label': 'Prescription Form'},
            {'value': 'other', 'label': 'Other'}
        ]
    }
    return render(request, 'admin/edit_template.html', context)


# ------------------------------
# AI Scribe and Form Automation Endpoints
# ------------------------------

def ai_scribe_dashboard(request):
    context = {
        'active_section': 'ai_scribe',
        'provider_name': 'Dr. Provider',
        'recent_transcriptions': [
            {
                'id': 1,
                'patient_name': 'Jane Doe',
                'appointment_type': 'Consultation',
                'timestamp': 'Today, 9:15 AM',
                'summary': 'Patient presented with symptoms of...'
            },
            {
                'id': 2,
                'patient_name': 'John Smith',
                'appointment_type': 'Follow-up',
                'timestamp': 'Yesterday, 3:30 PM',
                'summary': 'Follow-up for prescription adjustment...'
            }
        ]
    }
    return render(request, "provider/ai_scribe_dashboard.html", context)


@require_POST
def start_recording(request):
    appointment_id = request.POST.get('appointment_id')
    if not appointment_id:
        return JsonResponse({'success': False, 'error': 'Appointment ID is required'}, status=400)
    result = AIScribeService.start_recording(appointment_id)
    if result.get('success'):
        return JsonResponse({'success': True, 'recording': result.get('recording')})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)


@require_POST
def stop_recording(request):
    recording_id = request.POST.get('recording_id')
    if not recording_id:
        return JsonResponse({'success': False, 'error': 'Recording ID is required'}, status=400)
    result = AIScribeService.stop_recording(recording_id)
    if result.get('success'):
        return JsonResponse({'success': True, 'recording': result.get('recording')})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)


def get_transcription(request, recording_id):
    result = AIScribeService.process_transcription(recording_id)
    if result.get('success'):
        return JsonResponse({'success': True, 'transcription': result})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)


def generate_clinical_note(request, transcription_id):
    result = AIScribeService.generate_clinical_notes(transcription_id)
    if result.get('success'):
        return JsonResponse({'success': True, 'clinical_note': result.get('clinical_note')})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)


def view_clinical_note(request, note_id):
    note = {
        'id': note_id,
        'patient_name': 'Jane Doe',
        'appointment_date': 'April 3, 2025',
        'content': (
            "SUBJECTIVE:\nPatient presents with complaints of headache and fatigue for the past week.\n\n"
            "OBJECTIVE:\nVital signs stable. No fever. No neck stiffness or neurological deficits.\n\n"
            "ASSESSMENT:\nMigraine headache, consistent with patient's history.\n\n"
            "PLAN:\n1. Continue current medication.\n2. Increase water intake.\n"
            "3. Follow up in 2 weeks if symptoms persist."
        )
    }
    context = {
        'active_section': 'ai_scribe',
        'provider_name': 'Dr. Provider',
        'note': note
    }
    return render(request, 'provider/view_clinical_note.html', context)


@require_POST
def edit_clinical_note(request, note_id):
    content = request.POST.get('content')
    if not content:
        return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
    # Update clinical note in the database (implementation needed)
    return JsonResponse({'success': True, 'note_id': note_id})


def forms_dashboard(request):
    provider_id = 1
    templates_result = FormAutomationService.get_available_templates()
    patients = ProviderRepository.get_patients(provider_id)
    if not templates_result.get('success'):
        messages.error(request, f"Error loading templates: {templates_result.get('error', 'Unknown error')}")
    recent_documents = [
        {
            'id': 1,
            'template_name': 'Lab Requisition',
            'patient_name': 'Jane Doe',
            'created_at': 'Today, 11:23 AM',
            'status': 'Completed'
        },
        {
            'id': 2,
            'template_name': 'Sick Note',
            'patient_name': 'John Smith',
            'created_at': 'Yesterday, 3:45 PM',
            'status': 'Draft'
        },
        {
            'id': 3,
            'template_name': 'Specialist Referral',
            'patient_name': 'Emily Williams',
            'created_at': 'March 30, 2025',
            'status': 'Sent'
        }
    ]
    context = {
        'active_section': 'forms',
        'provider_name': 'Dr. Provider',
        'templates': templates_result.get('templates', []),
        'patients': patients,
        'recent_documents': recent_documents
    }
    return render(request, "provider/forms_dashboard.html", context)


def create_form(request, template_id):
    template_result = FormAutomationService.get_template_by_id(template_id)
    if not template_result.get('success'):
        messages.error(request, f"Error loading template: {template_result.get('error', 'Unknown error')}")
        return redirect('forms_dashboard')
    if request.method == 'POST':
        form_data = request.POST.dict()
        document_result = FormAutomationService.create_document(
            template_id=template_id,
            form_data=form_data,
            created_by_id=request.user.id
        )
        if document_result.get('success'):
            document_id = document_result['document']['id']
            messages.success(request, "Document created successfully!")
            return redirect('view_document', document_id=document_id)
        else:
            messages.error(request, f"Error creating document: {document_result.get('error', 'Unknown error')}")
    patient_id = request.GET.get('patient_id')
    form_data = {}
    if patient_id:
        auto_populate_result = FormAutomationService.auto_populate_form(
            template_id=template_id,
            patient_id=patient_id,
            provider_id=request.user.id
        )
        if auto_populate_result.get('success'):
            form_data = auto_populate_result.get('form_data', {})
    context = {
        'active_section': 'forms',
        'provider_name': 'Dr. Provider',
        'template': template_result.get('template'),
        'form_data': form_data,
        'patients': [
            {'id': 1, 'name': 'Jane Doe'},
            {'id': 2, 'name': 'John Smith'},
            {'id': 3, 'name': 'Robert Johnson'},
            {'id': 4, 'name': 'Emily Williams'}
        ]
    }
    return render(request, 'provider/create_form.html', context)


def view_document(request, document_id):
    render_result = FormAutomationService.render_document(document_id)
    if not render_result.get('success'):
        messages.error(request, f"Error rendering document: {render_result.get('error', 'Unknown error')}")
        return redirect('forms_dashboard')
    context = {
        'active_section': 'forms',
        'provider_name': 'Dr. Provider',
        'document_id': document_id,
        'html_content': render_result.get('html_content'),
        'pdf_available': render_result.get('pdf_available')
    }
    return render(request, 'provider/view_document.html', context)


def download_document_pdf(request, document_id):
    render_result = FormAutomationService.render_document(document_id)
    if not render_result.get('success'):
        messages.error(request, f"Error rendering document: {render_result.get('error', 'Unknown error')}")
        return redirect('forms_dashboard')
    response = HttpResponse(b'PDF content would go here', content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="document_{document_id}.pdf"'
    return response


@require_POST
def update_document_status(request, document_id):
    status_value = request.POST.get('status')
    if not status_value:
        return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)
    result = FormAutomationService.update_document_status(
        document_id=document_id,
        status=status_value,
        updated_by_id=request.user.id
    )
    if result.get('success'):
        return JsonResponse({'success': True, 'document': result.get('document')})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)
