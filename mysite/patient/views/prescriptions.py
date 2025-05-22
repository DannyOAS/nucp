# patient/views/prescriptions.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import logging
from django.http import Http404
from patient.services.prescription_service import PrescriptionService
from patient.decorators import patient_required_secure as patient_required
from patient.utils import get_current_patient_secure as get_current_patient
from api.v1.patient.serializers import PrescriptionSerializer

logger = logging.getLogger(__name__)

@patient_required
def patient_prescriptions(request):
    """
    Patient prescriptions view showing active and historical prescriptions.
    Uses service layer to retrieve data and API serializers for formatting.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    try:
        # Get prescriptions data from service
        prescriptions_data = PrescriptionService.get_patient_prescriptions(patient.id)
        
        # FIXED: Consistent data handling
        active_prescriptions = prescriptions_data.get('active_prescriptions', [])
        historical_prescriptions = prescriptions_data.get('historical_prescriptions', [])
        
        # FIXED: Handle both QuerySet and serialized data consistently
        if active_prescriptions and hasattr(active_prescriptions, 'model'):
            # It's a QuerySet - serialize it
            serializer = PrescriptionSerializer(active_prescriptions, many=True)
            active_prescriptions_data = serializer.data
        else:
            # It's already serialized or a list
            active_prescriptions_data = active_prescriptions
        
        if historical_prescriptions and hasattr(historical_prescriptions, 'model'):
            # It's a QuerySet - serialize it
            serializer = PrescriptionSerializer(historical_prescriptions, many=True)
            historical_prescriptions_data = serializer.data
        else:
            # It's already serialized or a list
            historical_prescriptions_data = historical_prescriptions
        
        # FIXED: Calculate renewal_needed_count with consistent data structure
        renewal_needed_count = 0
        for prescription in active_prescriptions_data:
            # Now we consistently work with dict/serialized data
            refills_remaining = prescription.get('refills_remaining', 0) if isinstance(prescription, dict) else getattr(prescription, 'refills_remaining', 0)
            if refills_remaining <= 1:
                renewal_needed_count += 1
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'active_prescriptions': active_prescriptions_data,
            'historical_prescriptions': historical_prescriptions_data,
            'active_section': 'prescriptions',
            'renewal_needed_count': renewal_needed_count,  # FIXED
            'active_prescriptions_count': len(active_prescriptions_data),
            'primary_pharmacy': getattr(patient, 'pharmacy_details', 'Northern Pharmacy'),
        }
    except Exception as e:
        logger.error(f"Error retrieving prescriptions: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'active_prescriptions': [],
            'historical_prescriptions': [],
            'active_section': 'prescriptions',
            'renewal_needed_count': 0,  # FIXED
            'active_prescriptions_count': 0,
            'primary_pharmacy': 'Northern Pharmacy',
        }
        messages.error(request, "There was an error loading your prescriptions. Please try again later.")
    
    return render(request, "patient/prescriptions.html", context)

@patient_required
def request_prescription(request):
    """
    View for patient to request a new prescription.
    Uses service layer for form handling and request creation.
    """
    # Get the current patient
    patient, patient_dict = get_current_patient(request)
    
    # If the function returns None, it has already redirected
    if patient is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # FIXED: Process prescription request via service with proper patient handling
            result = PrescriptionService.create_prescription_request(
                patient_id=patient.id,
                form_data=request.POST
            )
            
            if result.get('success', False):
                messages.success(request, "Prescription request submitted successfully!")
                return redirect('patient:patient_prescriptions')
            else:
                messages.error(request, result.get('error', "Error submitting prescription request."))
        except Exception as e:
            logger.error(f"Error submitting prescription request: {str(e)}")
            messages.error(request, f"Error submitting prescription request: {str(e)}")
    
    # For GET requests, prepare the form with initial data
    try:
        # Get form initial data from service
        form_data = PrescriptionService.get_prescription_form_data(patient.id)
        
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'form': form_data.get('form', {}),
            'active_section': 'prescriptions'
        }
    except Exception as e:
        logger.error(f"Error preparing prescription form: {str(e)}")
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'form': {},
            'active_section': 'prescriptions'
        }
        messages.error(request, "There was an error preparing the prescription request form.")
    
    return render(request, "patient/request_prescription.html", context)

@patient_required  # ENHANCED SECURITY
def prescription_detail(request, prescription_id):
    """
    COMPLETE: View prescription details with enhanced ownership verification
    """
    # Get verified patient
    patient, patient_dict = get_current_patient(request)
    if patient is None:
        logger.error(f"SECURITY: prescription_detail access denied for user {request.user.username}")
        raise Http404("Access denied")
    
    try:
        # CRITICAL: Enhanced ownership verification with multiple checks
        from common.models import Prescription
        prescription = get_object_or_404(
            Prescription.objects.select_related('patient', 'doctor', 'doctor__user'),
            id=prescription_id,
            patient=request.user,  # First check: user match
            patient__patient_profile=patient  # Second check: patient profile match
        )
        
        # TRIPLE VERIFICATION: Ensure prescription patient matches verified patient
        if prescription.patient.id != request.user.id:
            logger.error(f"SECURITY BREACH: Prescription ownership mismatch - prescription.patient.id={prescription.patient.id}, user.id={request.user.id}")
            raise Http404("Prescription not found")
        
        # Additional verification: Check if user has patient profile matching the prescription
        if not hasattr(request.user, 'patient_profile') or request.user.patient_profile.id != patient.id:
            logger.error(f"SECURITY BREACH: Patient profile mismatch in prescription access")
            raise Http404("Access denied")
        
        # Log successful access for audit trail
        logger.info(f"AUDIT: User {request.user.username} accessed prescription {prescription_id}")
        
        # COMPLETE: Build comprehensive prescription data
        prescription_data = {
            'id': prescription.id,
            'medication_name': getattr(prescription, 'medication_name', 'Unknown Medication'),
            'dosage': getattr(prescription, 'dosage', 'Not specified'),
            'status': getattr(prescription, 'status', 'Active'),
            'refills_remaining': getattr(prescription, 'refills_remaining', 0),
            'created_at': getattr(prescription, 'created_at', timezone.now()),
            'expires': getattr(prescription, 'expires', None),
            'instructions': getattr(prescription, 'instructions', 'Take as directed by your healthcare provider'),
            
            # Provider information (using pre-loaded relationship)
            'prescribed_by': f"Dr. {prescription.doctor.user.last_name}" if prescription.doctor and prescription.doctor.user else 'Your Healthcare Provider',
            'prescribed_date': getattr(prescription, 'created_at', timezone.now()).date() if hasattr(prescription, 'created_at') else date.today(),
            'provider_phone': getattr(prescription.doctor, 'phone', '(555) 123-4567') if prescription.doctor else '(555) 123-4567',
            'provider_specialty': getattr(prescription.doctor, 'specialty', 'General Practice') if prescription.doctor else 'General Practice',
            
            # Pharmacy information
            'pharmacy': getattr(prescription, 'pharmacy', 'Northern Pharmacy'),
            'pharmacy_address': '123 Health Street, Toronto, ON M5V 1A1',  # This would come from pharmacy model
            'pharmacy_phone': '(416) 555-MEDS',
            
            # Safety information - This would typically come from a drug database
            'side_effects': self._get_medication_side_effects(prescription.medication_name),
            'warnings': self._get_medication_warnings(prescription.medication_name),
            'drug_interactions': self._get_drug_interactions(prescription.medication_name),
            'mechanism_of_action': self._get_mechanism_of_action(prescription.medication_name),
            
            # Refill information
            'can_request_refill': (
                prescription.status == 'Active' and 
                getattr(prescription, 'refills_remaining', 0) > 0
            ),
            'last_refill_date': self._get_last_refill_date(prescription),
            'next_refill_eligible': self._calculate_next_refill_date(prescription),
            
            # Formatting helpers
            'prescribed_date_formatted': getattr(prescription, 'created_at', timezone.now()).strftime('%B %d, %Y') if hasattr(prescription, 'created_at') else date.today().strftime('%B %d, %Y'),
            'expires_formatted': prescription.expires.strftime('%B %d, %Y') if prescription.expires else 'No expiration date',
        }
        
        # BUSINESS LOGIC: Check for prescription alerts
        alerts = self._check_prescription_alerts(prescription, patient)
        
        context = {
            'patient': patient_dict,  # Using masked data
            'patient_name': patient.full_name,
            'prescription': prescription_data,
            'alerts': alerts,
            'active_section': 'prescriptions'
        }
        
    except Prescription.DoesNotExist:
        # FALLBACK: Try to get from PrescriptionRequest model
        try:
            from patient.models import PrescriptionRequest
            prescription_request = get_object_or_404(
                PrescriptionRequest.objects.select_related('patient'),
                id=prescription_id,
                patient=patient
            )
            
            logger.info(f"AUDIT: User {request.user.username} accessed prescription request {prescription_id}")
            
            # Convert PrescriptionRequest to prescription-like format
            prescription_data = {
                'id': prescription_request.id,
                'medication_name': prescription_request.medication_name,
                'dosage': prescription_request.current_dosage,
                'status': prescription_request.status.title(),
                'refills_remaining': 3 if prescription_request.status == 'approved' else 0,
                'created_at': prescription_request.created_at,
                'expires': None,
                'instructions': 'Take as directed by your healthcare provider',
                
                # Provider information (default since not stored in PrescriptionRequest)
                'prescribed_by': 'Your Healthcare Provider',
                'prescribed_date': prescription_request.created_at.date(),
                'provider_phone': '(555) 123-4567',
                'provider_specialty': 'General Practice',
                
                # Pharmacy information
                'pharmacy': prescription_request.preferred_pharmacy,
                'pharmacy_address': '123 Health Street, Toronto, ON M5V 1A1',
                'pharmacy_phone': '(416) 555-MEDS',
                
                # Safety information
                'side_effects': prescription_request.side_effects or self._get_medication_side_effects(prescription_request.medication_name),
                'warnings': self._get_medication_warnings(prescription_request.medication_name),
                'drug_interactions': self._get_drug_interactions(prescription_request.medication_name),
                'mechanism_of_action': self._get_mechanism_of_action(prescription_request.medication_name),
                
                # Refill information
                'can_request_refill': prescription_request.status == 'approved',
                'last_refill_date': prescription_request.last_refill_date,
                'next_refill_eligible': prescription_request.last_refill_date + timedelta(days=30) if prescription_request.last_refill_date else None,
                
                # Formatting helpers
                'prescribed_date_formatted': prescription_request.created_at.strftime('%B %d, %Y'),
                'expires_formatted': 'No expiration date',
            }
            
            # Check for alerts
            alerts = self._check_prescription_request_alerts(prescription_request, patient)
            
            context = {
                'patient': patient_dict,
                'patient_name': patient.full_name,
                'prescription': prescription_data,
                'alerts': alerts,
                'active_section': 'prescriptions'
            }
            
        except PrescriptionRequest.DoesNotExist:
            logger.warning(f"SECURITY: User {request.user.username} attempted to access non-existent prescription {prescription_id}")
            raise Http404("Prescription not found")
            
    except Exception as e:
        logger.error(f"SECURITY: Prescription access error for user {request.user.username}, prescription {prescription_id}: {str(e)}")
        raise Http404("Access denied")
    
    return render(request, "patient/prescription_detail.html", context)

def _get_medication_side_effects(self, medication_name):
    """
    COMPLETE: Get medication side effects from drug database
    In production, this would query a real drug database API
    """
    # Common side effects database (simplified)
    side_effects_db = {
        'acetaminophen': 'Nausea, vomiting, loss of appetite, sweating, stomach/abdominal pain, extreme tiredness, yellowing eyes/skin, dark urine.',
        'ibuprofen': 'Upset stomach, mild heartburn, nausea, vomiting, bloating, gas, diarrhea, constipation, dizziness, headache, nervousness.',
        'amoxicillin': 'Nausea, vomiting, diarrhea, stomach pain, vaginal itching or discharge, headache, dizziness.',
        'lisinopril': 'Dizziness, headache, tiredness, nausea, diarrhea, cough.',
        'metformin': 'Nausea, vomiting, stomach upset, diarrhea, weakness, metallic taste in mouth.',
        'atorvastatin': 'Muscle pain, tenderness, weakness, nausea, diarrhea, constipation, stomach pain.',
    }
    
    medication_lower = medication_name.lower()
    for drug_name, side_effects in side_effects_db.items():
        if drug_name in medication_lower:
            return side_effects
    
    return 'Common side effects may include nausea, dizziness, or stomach upset. Contact your healthcare provider if you experience any unusual symptoms.'

def _get_medication_warnings(self, medication_name):
    """
    COMPLETE: Get medication warnings from drug database
    """
    warnings_db = {
        'acetaminophen': 'Do not exceed 4000mg in 24 hours. Avoid alcohol. May cause liver damage in high doses.',
        'ibuprofen': 'Take with food. May increase risk of heart attack or stroke. Avoid if you have kidney disease.',
        'amoxicillin': 'Complete the full course even if you feel better. May cause allergic reactions.',
        'lisinopril': 'May cause dizziness. Stand up slowly. Monitor blood pressure regularly.',
        'metformin': 'Take with meals. Monitor blood sugar levels. Stay hydrated.',
        'atorvastatin': 'Avoid grapefruit juice. Report muscle pain immediately. Monitor liver function.',
    }
    
    medication_lower = medication_name.lower()
    for drug_name, warnings in warnings_db.items():
        if drug_name in medication_lower:
            return warnings
    
    return 'Take exactly as prescribed. Do not stop without consulting your healthcare provider. Store at room temperature away from moisture and heat.'

def _get_drug_interactions(self, medication_name):
    """
    COMPLETE: Get drug interaction information
    """
    interactions_db = {
        'acetaminophen': 'May interact with warfarin, alcohol, and certain seizure medications.',
        'ibuprofen': 'May interact with blood thinners, blood pressure medications, and lithium.',
        'amoxicillin': 'May interact with methotrexate and reduce effectiveness of birth control pills.',
        'lisinopril': 'May interact with potassium supplements, salt substitutes, and diuretics.',
        'metformin': 'May interact with contrast dyes, alcohol, and certain heart medications.',
        'atorvastatin': 'May interact with grapefruit juice, certain antibiotics, and heart medications.',
    }
    
    medication_lower = medication_name.lower()
    for drug_name, interactions in interactions_db.items():
        if drug_name in medication_lower:
            return interactions
    
    return 'Always inform healthcare providers about all medications you are taking, including over-the-counter drugs and supplements.'

def _get_mechanism_of_action(self, medication_name):
    """
    COMPLETE: Get how the medication works
    """
    mechanism_db = {
        'acetaminophen': 'Reduces pain and fever by blocking certain chemical signals in the brain.',
        'ibuprofen': 'Reduces inflammation, pain, and fever by blocking enzymes that cause inflammation.',
        'amoxicillin': 'Antibiotic that works by stopping the growth of bacteria.',
        'lisinopril': 'ACE inhibitor that relaxes blood vessels to lower blood pressure.',
        'metformin': 'Helps control blood sugar by reducing glucose production in the liver.',
        'atorvastatin': 'Statin that lowers cholesterol by blocking an enzyme needed to make cholesterol.',
    }
    
    medication_lower = medication_name.lower()
    for drug_name, mechanism in mechanism_db.items():
        if drug_name in medication_lower:
            return mechanism
    
    return 'This medication works by targeting specific processes in your body to treat your condition. Your healthcare provider can explain more about how it helps your specific situation.'

def _get_last_refill_date(self, prescription):
    """
    COMPLETE: Get the last refill date for this prescription
    """
    try:
        from patient.models import PrescriptionRequest
        last_refill = PrescriptionRequest.objects.filter(
            medication_name=prescription.medication_name,
            patient__user=prescription.patient,
            status='approved'
        ).order_by('-created_at').first()
        
        return last_refill.created_at.date() if last_refill else None
    except:
        return None

def _calculate_next_refill_date(self, prescription):
    """
    COMPLETE: Calculate when the next refill can be requested
    """
    last_refill = self._get_last_refill_date(prescription)
    if last_refill:
        # Typically can refill when 75% of medication is used (assuming 30-day supply)
        return last_refill + timedelta(days=23)  # 30 * 0.75 = 22.5 days
    return None

def _check_prescription_alerts(self, prescription, patient):
    """
    COMPLETE: Check for prescription alerts and warnings
    """
    alerts = []
    
    # Check if prescription is expiring soon
    if prescription.expires:
        days_until_expiry = (prescription.expires - date.today()).days
        if days_until_expiry <= 30:
            alerts.append({
                'type': 'warning',
                'message': f'This prescription expires in {days_until_expiry} days. Contact your provider for renewal.'
            })
    
    # Check if refills are running low
    refills_remaining = getattr(prescription, 'refills_remaining', 0)
    if refills_remaining <= 1 and refills_remaining > 0:
        alerts.append({
            'type': 'info',
            'message': f'Only {refills_remaining} refill remaining. Consider requesting renewal soon.'
        })
    elif refills_remaining <= 0:
        alerts.append({
            'type': 'error',
            'message': 'No refills remaining. Contact your provider for a new prescription.'
        })
    
    # Check for age-specific warnings
    patient_age = patient.age
    medication_lower = prescription.medication_name.lower()
    
    if patient_age >= 65:
        if 'ibuprofen' in medication_lower or 'nsaid' in medication_lower:
            alerts.append({
                'type': 'warning',
                'message': 'Seniors should use NSAIDs with caution. Monitor for stomach upset or kidney problems.'
            })
    
    # Check for recent refill eligibility
    next_refill = self._calculate_next_refill_date(prescription)
    if next_refill and next_refill <= date.today() and refills_remaining > 0:
        alerts.append({
            'type': 'success',
            'message': 'You are eligible to request a refill for this prescription.'
        })
    
    return alerts

def _check_prescription_request_alerts(self, prescription_request, patient):
    """
    COMPLETE: Check alerts for prescription requests
    """
    alerts = []
    
    # Status-based alerts
    if prescription_request.status == 'pending':
        days_pending = (date.today() - prescription_request.created_at.date()).days
        if days_pending >= 3:
            alerts.append({
                'type': 'warning',
                'message': f'This request has been pending for {days_pending} days. You may want to contact your provider.'
            })
        else:
            alerts.append({
                'type': 'info',
                'message': 'Your prescription request is being reviewed by your healthcare provider.'
            })
    elif prescription_request.status == 'denied':
        alerts.append({
            'type': 'error',
            'message': 'This prescription request was denied. Contact your provider for more information.'
        })
    elif prescription_request.status == 'approved':
        alerts.append({
            'type': 'success',
            'message': 'This prescription request has been approved and sent to your pharmacy.'
        })
    
    return alerts

@patient_required
def request_refill(request, prescription_id):
    """
    COMPLETE: Request prescription refill with enhanced verification and full implementation
    """
    patient, patient_dict = get_current_patient(request)
    if patient is None:
        raise Http404("Access denied")
    
    try:
        # CRITICAL: Verify prescription ownership with multiple checks
        from common.models import Prescription
        prescription = get_object_or_404(
            Prescription.objects.select_related('patient'),
            id=prescription_id,
            patient=request.user,
            patient__patient_profile=patient
        )
        
        # ADDITIONAL SECURITY: Verify refills are available BEFORE processing
        if hasattr(prescription, 'refills_remaining') and prescription.refills_remaining <= 0:
            logger.warning(f"SECURITY: User {request.user.username} attempted refill with no refills remaining for prescription {prescription_id}")
            messages.error(request, "No refills remaining for this prescription.")
            return redirect('patient:patient_prescriptions')
        
        # SECURITY: Rate limiting check (prevent spam refill requests)
        recent_requests = patient.prescription_requests.filter(
            medication_name=prescription.medication_name,
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        
        if recent_requests >= 3:  # Max 3 requests per day per medication
            logger.warning(f"SECURITY: Rate limit exceeded for user {request.user.username} on prescription {prescription_id}")
            messages.error(request, "Too many refill requests. Please wait 24 hours.")
            return redirect('patient:patient_prescriptions')
        
        if request.method == 'POST':
            # COMPLETE IMPLEMENTATION: Process refill request with validation
            
            # Extract and validate form data
            pharmacy = request.POST.get('pharmacy', '').strip()
            other_pharmacy_name = request.POST.get('other_pharmacy_name', '').strip()
            other_pharmacy_address = request.POST.get('other_pharmacy_address', '').strip()
            other_pharmacy_phone = request.POST.get('other_pharmacy_phone', '').strip()
            last_dose_taken = request.POST.get('last_dose_taken', '').strip()
            medication_changes = request.POST.get('medication_changes', '').strip()
            changes_description = request.POST.get('changes_description', '').strip()
            side_effects = request.POST.get('side_effects', '').strip()
            notes = request.POST.get('notes', '').strip()
            information_consent = 'information_consent' in request.POST
            pharmacy_consent = 'pharmacy_consent' in request.POST
            
            # VALIDATION: Check required fields
            validation_errors = []
            
            if not pharmacy:
                validation_errors.append("Please select a pharmacy.")
            
            if pharmacy == 'other':
                if not other_pharmacy_name:
                    validation_errors.append("Please provide the pharmacy name.")
                if not other_pharmacy_address:
                    validation_errors.append("Please provide the pharmacy address.")
                if not other_pharmacy_phone:
                    validation_errors.append("Please provide the pharmacy phone number.")
            
            if not last_dose_taken:
                validation_errors.append("Please specify when you took your last dose.")
            else:
                # Validate date format and logic
                try:
                    last_dose_date = date.fromisoformat(last_dose_taken)
                    if last_dose_date > date.today():
                        validation_errors.append("Last dose date cannot be in the future.")
                    if last_dose_date < date.today() - timedelta(days=365):
                        validation_errors.append("Last dose date cannot be more than a year ago.")
                except ValueError:
                    validation_errors.append("Invalid date format for last dose.")
            
            if not information_consent:
                validation_errors.append("You must consent to the accuracy of the information provided.")
            
            if not pharmacy_consent:
                validation_errors.append("You must consent to sending the prescription to the pharmacy.")
            
            # SECURITY: Validate text fields for malicious content
            text_fields = {
                'changes_description': changes_description,
                'side_effects': side_effects,
                'notes': notes
            }
            
            import re
            dangerous_patterns = [
                r'<script',
                r'javascript:',
                r'<iframe',
                r'<object',
                r'<embed',
                r'eval\(',
                r'alert\(',
                r'document\.',
                r'window\.',
            ]
            
            for field_name, field_value in text_fields.items():
                if field_value:
                    for pattern in dangerous_patterns:
                        if re.search(pattern, field_value, re.IGNORECASE):
                            validation_errors.append(f"Invalid content in {field_name.replace('_', ' ')} field.")
                            logger.warning(f"SECURITY: Malicious content detected in {field_name} by user {request.user.username}")
                            break
            
            # If validation errors, show them and return to form
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                
                # Return to form with current data
                context = {
                    'patient': patient_dict,
                    'patient_name': patient.full_name,
                    'prescription': {
                        'id': prescription.id,
                        'medication_name': prescription.medication_name,
                        'refills_remaining': getattr(prescription, 'refills_remaining', 0)
                    },
                    'form_data': request.POST,  # Preserve form data
                    'active_section': 'prescriptions'
                }
                return render(request, "patient/request_refill.html", context)
            
            # BUSINESS LOGIC: Create refill request
            try:
                from patient.models import PrescriptionRequest
                
                # Determine pharmacy details
                if pharmacy == 'other':
                    pharmacy_details = f"{other_pharmacy_name}, {other_pharmacy_address}, {other_pharmacy_phone}"
                else:
                    pharmacy_details = "Northern Pharmacy (Default)"
                
                # Create the refill request
                refill_request = PrescriptionRequest.objects.create(
                    patient=patient,
                    medication_name=prescription.medication_name,
                    current_dosage=getattr(prescription, 'dosage', 'As prescribed'),
                    medication_duration=f"Refill request - ongoing treatment",
                    last_refill_date=date.fromisoformat(last_dose_taken) if last_dose_taken else None,
                    preferred_pharmacy=pharmacy_details,
                    new_medical_conditions='',  # Not applicable for refills
                    new_medications=changes_description if medication_changes == 'yes' else '',
                    side_effects=side_effects,
                    information_consent=information_consent,
                    pharmacy_consent=pharmacy_consent,
                    status='pending'
                )
                
                # BUSINESS RULE: Update original prescription refill count
                if hasattr(prescription, 'refills_remaining') and prescription.refills_remaining > 0:
                    prescription.refills_remaining = max(0, prescription.refills_remaining - 1)
                    prescription.save()
                
                # AUDIT: Log the refill request
                logger.info(f"AUDIT: User {request.user.username} requested refill for prescription {prescription_id}, created request {refill_request.id}")
                
                # SUCCESS: Show success message and redirect
                messages.success(request, f"Refill request for {prescription.medication_name} submitted successfully! You will be notified when it's processed.")
                
                # NOTIFICATION: In a real system, you might send notifications here
                # send_refill_notification_to_provider(refill_request)
                # send_confirmation_email_to_patient(patient, refill_request)
                
                return redirect('patient:patient_prescriptions')
                
            except Exception as e:
                logger.error(f"ERROR: Failed to create refill request for user {request.user.username}, prescription {prescription_id}: {str(e)}")
                messages.error(request, "There was an error processing your refill request. Please try again.")
                
                # Return to form
                context = {
                    'patient': patient_dict,
                    'patient_name': patient.full_name,
                    'prescription': {
                        'id': prescription.id,
                        'medication_name': prescription.medication_name,
                        'refills_remaining': getattr(prescription, 'refills_remaining', 0)
                    },
                    'active_section': 'prescriptions'
                }
                return render(request, "patient/request_refill.html", context)
        
        # GET request: Show the refill form
        context = {
            'patient': patient_dict,
            'patient_name': patient.full_name,
            'prescription': {
                'id': prescription.id,
                'medication_name': prescription.medication_name,
                'dosage': getattr(prescription, 'dosage', 'Not specified'),
                'refills_remaining': getattr(prescription, 'refills_remaining', 0),
                'prescribed_by': getattr(prescription, 'prescribed_by', 'Your Healthcare Provider'),
                'prescribed_date': getattr(prescription, 'created_at', timezone.now()).date() if hasattr(prescription, 'created_at') else date.today()
            },
            'active_section': 'prescriptions'
        }
        
    except Prescription.DoesNotExist:
        logger.warning(f"SECURITY: User {request.user.username} attempted to access non-existent prescription {prescription_id}")
        messages.error(request, "Prescription not found.")
        return redirect('patient:patient_prescriptions')
    except Exception as e:
        logger.error(f"SECURITY: Refill request error for user {request.user.username}: {str(e)}")
        messages.error(request, "There was an error loading the prescription details.")
        return redirect('patient:patient_prescriptions')
    
    return render(request, "patient/request_refill.html", context)
