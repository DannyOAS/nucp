#!/usr/bin/env python3
import os
import sys
import logging
import json
import django

# Set up project root for your Django project and add it to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("Added project root:", project_root)

# No need to add frappe paths since ERPNext (frappe) is on a different server

# Set Django settings module and initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

import requests
from django.conf import settings

class ERPNextClient:
    def __init__(self):
        # Use settings to override default values, if desired
        self.base_url = getattr(settings, "ERPNEXT_URL", "https://u2.isnord.ca")
        self.api_key = getattr(settings, "ERP_API_KEY", "e7e440ba311946c")
        self.api_secret = getattr(settings, "ERP_API_SECRET", "dc461decd332261")

    @property
    def headers(self):
        return {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def create_patient(self, patient_data):
        """
        Create a patient record in ERPNext using the REST API.
        """
        erp_patient_data = {
            "doctype": "Patient",
            "first_name": patient_data.get("first_name"),
            "last_name": patient_data.get("last_name"),
            "email": patient_data.get("email"),
            "mobile": patient_data.get("primary_phone"),
            "dob": patient_data.get("date_of_birth"),
            "sex": patient_data.get("sex") or "Male",
            "user": patient_data.get("email")  # Link patient to user via email
        }

        logger.debug(f"ERP patient payload: {erp_patient_data}")

        url = self.base_url.rstrip("/") + "/api/resource/Patient"
        try:
            response = requests.post(url, headers=self.headers, json=erp_patient_data, timeout=10)
            response.raise_for_status()
            logger.info(f"Patient created in ERPNext: {response.json().get('data', {}).get('name')}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"ERPNext API Error: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"ERPNext Error Response: {e.response.text}")
            raise

if __name__ == "__main__":
    # Define test patient data
    test_patient = {
        'first_name': 'Ayrton',
        'last_name': 'Patient1',
        'email': 'ayrtonpatient1@example.com',
        'primary_phone': '523-156-7890',
        'date_of_birth': '1991-02-01',
        'sex': 'Male',
    }
    
    logger.info("Attempting to create test patient with the following data:")
    logger.info(json.dumps(test_patient, indent=4))
    
    client = ERPNextClient()
    try:
        result = client.create_patient(test_patient)
        logger.info("Success! Patient created:")
        logger.info(json.dumps(result, indent=4))
        print("Patient creation result:")
        print(json.dumps(result, indent=4))
    except Exception as e:
        logger.error("Error creating patient: %s", e, exc_info=True)
        print("Error creating patient:")
        print(e)
