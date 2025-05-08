# patient/views/help.py
from django.shortcuts import render

def patient_help_center(request):
    """View for patient help center"""
    return render(request, 'patient/help_center.html')
