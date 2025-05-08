# patient/views/email.py
from django.shortcuts import render

def email_view(request):
    """View for patient email dashboard"""
    return render(request, 'patient/email.html')
