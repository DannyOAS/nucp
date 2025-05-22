# patient/templatetags/__init__.py
# Create this file (empty) to make templatetags a package

# patient/templatetags/patient_filters.py
from django import template
import re

register = template.Library()

@register.filter
def mask_ohip(ohip_number):
    """Mask OHIP number showing only last 3 digits"""
    if not ohip_number or len(ohip_number) < 4:
        return "****"
    return f"****-***-{ohip_number[-3:]}"

@register.filter  
def mask_phone(phone_number):
    """Mask phone number showing only last 4 digits"""
    if not phone_number:
        return "***-***-****"
    # Remove non-digits
    digits = re.sub(r'\D', '', phone_number)
    if len(digits) >= 4:
        return f"***-***-{digits[-4:]}"
    return "***-***-****"

@register.filter
def mask_email(email):
    """Mask email showing only first char and domain"""
    if not email or '@' not in email:
        return "***@***.com"
    local, domain = email.split('@', 1)
    if local:
        return f"{local[0]}***@{domain}"
    return "***@***.com"

@register.filter
def truncate_address(address):
    """Show only first line of address for privacy"""
    if not address:
        return "Address on file"
    lines = address.split('\n')
    return f"{lines[0]}..." if lines else "Address on file"
