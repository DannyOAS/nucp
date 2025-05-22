# STEP 1: Remove the Patient model from patient/validators.py
# The validators.py file should ONLY contain validation functions, not models

# patient/validators.py - CORRECTED VERSION (remove the Patient model)
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_ohip_number(value):
    """
    CRITICAL: Validate Ontario Health Card (OHIP) number format
    Format: 1234-567-890-AB (10 digits + 2 letters) or 1234567890AB
    """
    if not value:
        raise ValidationError(_('OHIP number is required.'))
    
    # Remove spaces and hyphens for validation
    clean_value = re.sub(r'[\s\-]', '', value.upper())
    
    # Check basic format: 10 digits followed by 2 letters
    if not re.match(r'^\d{10}[A-Z]{2}$', clean_value):
        raise ValidationError(
            _('Invalid OHIP number format. Must be 10 digits followed by 2 letters (e.g., 1234567890AB).')
        )
    
    # Additional validation: Check digit algorithm (simplified)
    digits = clean_value[:10]
    letters = clean_value[10:]
    
    # Basic checksum validation (you'd implement the actual OHIP algorithm)
    if sum(int(d) for d in digits) % 10 == 0 and letters == 'AA':
        raise ValidationError(_('Invalid OHIP number. Please check and try again.'))
    
    return clean_value

def validate_canadian_phone(value):
    """
    CRITICAL: Validate Canadian phone number format
    """
    if not value:
        return value
    
    # Remove all non-digits
    digits = re.sub(r'\D', '', value)
    
    # Must be 10 digits for Canadian numbers (or 11 with country code)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]  # Remove country code
    
    if len(digits) != 10:
        raise ValidationError(
            _('Invalid phone number. Must be 10 digits (e.g., 416-555-1234).')
        )
    
    # Area code validation (Canadian area codes)
    area_code = digits[:3]
    valid_area_codes = [
        '204', '226', '236', '249', '250', '289', '306', '343', '365', '403', '416', '418', '431', '437',
        '438', '450', '506', '514', '519', '548', '579', '581', '587', '604', '613', '639', '647', '672',
        '705', '709', '742', '778', '780', '782', '807', '819', '825', '867', '873', '902', '905'
    ]
    
    if area_code not in valid_area_codes:
        raise ValidationError(
            _('Invalid Canadian area code. Please enter a valid Canadian phone number.')
        )
    
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

def validate_medication_name(value):
    """
    CRITICAL: Validate medication name against dangerous inputs
    """
    if not value:
        raise ValidationError(_('Medication name is required.'))
    
    # Remove extra whitespace
    value = value.strip()
    
    if len(value) < 2:
        raise ValidationError(_('Medication name must be at least 2 characters.'))
    
    if len(value) > 200:
        raise ValidationError(_('Medication name must be less than 200 characters.'))
    
    # Check for suspicious patterns that might indicate injection attempts
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
        r'[\'"]\s*\+\s*[\'"]',  # String concatenation
        r'union\s+select',      # SQL injection
        r'drop\s+table',        # SQL injection
        r'delete\s+from',       # SQL injection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(_('Invalid medication name. Please enter a valid medication name.'))
    
    # Only allow letters, numbers, spaces, hyphens, parentheses, and common medical symbols
    if not re.match(r'^[a-zA-Z0-9\s\-\(\)\./,%]+$', value):
        raise ValidationError(
            _('Medication name contains invalid characters. Only letters, numbers, spaces, hyphens, parentheses, and basic punctuation are allowed.')
        )
    
    return value

def validate_dosage(value):
    """
    CRITICAL: Validate medication dosage format
    """
    if not value:
        return value
    
    value = value.strip()
    
    if len(value) > 100:
        raise ValidationError(_('Dosage must be less than 100 characters.'))
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'eval\(',
        r'alert\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(_('Invalid dosage format.'))
    
    # Allow common dosage formats: "10mg", "1 tablet", "2.5ml", "1/2 pill", etc.
    if not re.match(r'^[a-zA-Z0-9\s\-\(\)\./,%]+$', value):
        raise ValidationError(
            _('Dosage contains invalid characters. Please use standard dosage format (e.g., "10mg", "1 tablet").')
        )
    
    return value

def validate_postal_code(value):
    """
    CRITICAL: Validate Canadian postal code format
    """
    if not value:
        return value
    
    # Remove spaces and convert to uppercase
    value = re.sub(r'\s', '', value.upper())
    
    # Canadian postal code format: A1A1A1
    if not re.match(r'^[A-Z]\d[A-Z]\d[A-Z]\d$', value):
        raise ValidationError(
            _('Invalid postal code format. Must be in format A1A 1A1.')
        )
    
    # Format with space: A1A 1A1
    return f"{value[:3]} {value[3:]}"

# REMOVE EVERYTHING BELOW THIS LINE FROM validators.py
# The Patient and PrescriptionRequest models should ONLY be in models.py
