import requests

# Your API credentials
API_KEY = "74e1c529a3e6bb5"
API_SECRET = "7fde1ca12039908"
BASE_URL = "https://u2.isnord.ca"

def test_connection():
    # Authentication headers
    headers = {
        "Authorization": f"token {API_KEY}:{API_SECRET}",
        "Content-Type": "application/json"
    }

    try:
        # Test Patient API endpoint
        print("Testing API Connection...")

        # First, try to get version info (commonly accessible)
        version_response = requests.get(
            f"{BASE_URL}/api/method/frappe.utils.change_log.get_versions",
            headers=headers
        )
        print("\nVersion Check:")
        print(f"Status Code: {version_response.status_code}")
        print(f"Response: {version_response.text}")

        # Then try to access Patient doctype
        patient_response = requests.get(
            f"{BASE_URL}/api/resource/Patient",
            headers=headers
        )
        print("\nPatient API Check:")
        print(f"Status Code: {patient_response.status_code}")
        print(f"Response: {patient_response.text}")

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_connection()
