# test_api_versioning_auth.py
import requests
import json
from datetime import datetime

# Print header with timestamp
print(f"API Version Test - {datetime.now()}")

# Base URL of your API
base_url = "http://127.0.0.1:8000/api"

# Authentication token - Replace with a valid token
auth_token = "YOUR_AUTH_TOKEN_HERE"
auth_headers = {
    "Authorization": f"Token {auth_token}"
}

# Test the main API endpoints
print("--- Testing Core API (v1) ---")
endpoints = [
    "/v1/",
    "/v1/users/",
    "/v1/groups/"
]

for endpoint in endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=auth_headers)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} GET {base_url}{endpoint} - Status: {response.status_code}")
        
        # Display available endpoints for the root path
        if endpoint == "/v1/" and response.status_code == 200:
            data = response.json()
            print(f"Available endpoints: {list(data.keys())}")
            
        # Check for version info
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                first_item = data[0]
                if 'api_version' in first_item:
                    print(f"✓ Version info found: {first_item['api_version']}")
            elif isinstance(data, dict) and 'api_version' in data:
                print(f"✓ Version info found: {data['api_version']}")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)}")

# Test the patient API
print("\n--- Testing Patient API (v1) ---")
patient_endpoints = [
    "/v1/patient/",
    "/v1/patient/profile/",
    "/v1/patient/appointments/",
    "/v1/patient/prescriptions/",
    "/v1/patient/prescription-requests/",
    "/v1/patient/messages/"
]

for endpoint in patient_endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=auth_headers)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} GET {base_url}{endpoint} - Status: {response.status_code}")
        
        # For root endpoint, display available endpoints
        if endpoint == "/v1/patient/" and response.status_code == 200:
            data = response.json()
            print(f"Available endpoints: {list(data.keys())}")
            
        # Check for version info in a sample response
        if response.status_code == 200 and endpoint != "/v1/patient/":
            data = response.json()
            if isinstance(data, list) and data:
                first_item = data[0]
                if 'api_version' in first_item:
                    print(f"✓ Version info found: {first_item['api_version']}")
            elif isinstance(data, dict) and 'api_version' in data:
                print(f"✓ Version info found: {data['api_version']}")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)}")

# Test the provider API
print("\n--- Testing Provider API (v1) ---")
provider_endpoints = [
    "/v1/provider/",
    "/v1/provider/profile/",
    "/v1/provider/appointments/",
    "/v1/provider/prescriptions/",
    "/v1/provider/clinical-notes/",
    "/v1/provider/document-templates/",
    "/v1/provider/generated-documents/",
    "/v1/provider/recordings/",
    "/v1/provider/templates/",
    "/v1/provider/documents/",
    "/v1/provider/patients/",
    "/v1/provider/messages/"
]

for endpoint in provider_endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=auth_headers)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} GET {base_url}{endpoint} - Status: {response.status_code}")
        
        # For root endpoint, display available endpoints
        if endpoint == "/v1/provider/" and response.status_code == 200:
            data = response.json()
            print(f"Available endpoints: {list(data.keys())}")
            
        # Check for version info in a sample response
        if response.status_code == 200 and endpoint != "/v1/provider/":
            data = response.json()
            if isinstance(data, list) and data:
                first_item = data[0]
                if 'api_version' in first_item:
                    print(f"✓ Version info found: {first_item['api_version']}")
            elif isinstance(data, dict) and 'api_version' in data:
                print(f"✓ Version info found: {data['api_version']}")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)}")

# Test legacy API redirects
print("\n--- Testing Legacy API Redirects ---")
legacy_endpoints = [
    "/patient/", 
    "/provider/"
]

for endpoint in legacy_endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=auth_headers, allow_redirects=False)
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            status = "✅" if "/v1/" in location else "❌"
            print(f"{status} {endpoint} redirects properly - Status: {response.status_code}")
            print(f"Redirect target: {location}")
        else:
            print(f"❌ {endpoint} - Status: {response.status_code} (expected 302)")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {str(e)}")

print("Tests completed")
