import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ERPNextClient:
    def __init__(self):
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
        Create a patient record in ERPNext from the given patient_data dictionary.
        Ensure that the mandatory fields in ERPNext (like "sex") are supplied.
        """
        erp_patient_data = {
            "doctype": "Patient",
            "first_name": patient_data.get("first_name"),
            "last_name": patient_data.get("last_name"),
            "email": patient_data.get("email"),
            "mobile": patient_data.get("primary_phone"),
            "dob": patient_data.get("date_of_birth"),
            "sex": patient_data.get("sex") or "Male",  # Provide default if missing
            "user": patient_data.get("email"),
            # Map additional fields if needed:
            "address_line1": patient_data.get("address"),
            "ohip_number": patient_data.get("ohip_number"),
            "medication_list": patient_data.get("current_medications"),
            "allergies": patient_data.get("allergies"),
            "supplements": patient_data.get("supplements"),
            "pharmacy_details": patient_data.get("pharmacy_details"),
            "emergency_contact_name": patient_data.get("emergency_contact_name"),
            "emergency_contact_number": patient_data.get("emergency_contact_phone"),
            "emergency_contact_alternate_number": patient_data.get("emergency_contact_alternate_phone"),
            "virtual_care_consent": patient_data.get("virtual_care_consent"),
            "ehr_consent": patient_data.get("ehr_consent")
        }

        logger.debug(f"ERP patient payload: {erp_patient_data}")

        # Construct the API endpoint URL for Patient doctype
        url = self.base_url.rstrip("/") + "/api/resource/Patient"

        try:
            response = requests.post(url, headers=self.headers, json=erp_patient_data, timeout=10)
            response.raise_for_status()
            logger.info("Patient created in ERPNext: %s", response.json().get("data", {}).get("name"))
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("ERPNext API Error: %s", str(e))
            if hasattr(e.response, 'text'):
                logger.error("ERPNext Error Response: %s", e.response.text)
        raise
