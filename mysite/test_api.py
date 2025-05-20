import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
V1_API = f"{BASE_URL}/api/v1"
TOKEN = "ff60010b52da74d475a47ddc4300b5a0ba94d47f"  # Your working token

def test_endpoint(url, method="GET", data=None, expected_status=200):
    """Test a specific endpoint"""
    headers = {"Authorization": f"Token {TOKEN}"}
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    
    if response.status_code == expected_status:
        print(f"✅ {method} {url} - Status: {response.status_code}")
        return True, response.json() if response.content else None
    else:
        print(f"❌ {method} {url} - Expected: {expected_status}, Got: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return False, None

def test_core_api():
    """Test the core API endpoints under /api/v1/"""
    print("\n--- Testing Core API (v1) ---\n")
    
    # Test API root
    success, data = test_endpoint(f"{V1_API}/")
    if success and data:
        print(f"Available endpoints: {list(data.keys())}")
    
    # Test users endpoint
    test_endpoint(f"{V1_API}/users/")
    
    # Test groups endpoint
    test_endpoint(f"{V1_API}/groups/")

def test_patient_api():
    """Test the patient API endpoints under /api/v1/patient/"""
    print("\n--- Testing Patient API (v1) ---\n")
    
    # Test API root
    success, data = test_endpoint(f"{V1_API}/patient/")
    if success and data:
        print(f"Available endpoints: {list(data.keys())}")
        
        # Test each available endpoint
        for endpoint in data.keys():
            test_endpoint(f"{V1_API}/patient/{endpoint}/")

def test_provider_api():
    """Test the provider API endpoints under /api/v1/provider/"""
    print("\n--- Testing Provider API (v1) ---\n")
    
    # Test API root
    success, data = test_endpoint(f"{V1_API}/provider/")
    if success and data:
        print(f"Available endpoints: {list(data.keys())}")
        
        # Test each available endpoint
        for endpoint in data.keys():
            test_endpoint(f"{V1_API}/provider/{endpoint}/")

def test_legacy_redirects():
    """Test that legacy API paths redirect to versioned paths"""
    print("\n--- Testing Legacy API Redirects ---\n")
    
    # Test patient API redirect
    response = requests.get(
        f"{BASE_URL}/api/patient/",
        headers={"Authorization": f"Token {TOKEN}"},
        allow_redirects=False  # Don't follow redirects, just check status
    )
    
    if response.status_code in [301, 302]:
        print(f"✅ /api/patient/ redirects properly - Status: {response.status_code}")
        print(f"Redirect target: {response.headers.get('Location')}")
    else:
        print(f"❌ /api/patient/ does not redirect - Status: {response.status_code}")
    
    # Test provider API redirect
    response = requests.get(
        f"{BASE_URL}/api/provider/",
        headers={"Authorization": f"Token {TOKEN}"},
        allow_redirects=False  # Don't follow redirects, just check status
    )
    
    if response.status_code in [301, 302]:
        print(f"✅ /api/provider/ redirects properly - Status: {response.status_code}")
        print(f"Redirect target: {response.headers.get('Location')}")
    else:
        print(f"❌ /api/provider/ does not redirect - Status: {response.status_code}")

# Run the tests
if __name__ == "__main__":
    print(f"API Version Test - {datetime.now()}")
    test_core_api()
    test_patient_api()
    test_provider_api()
    test_legacy_redirects()
    print("\nTests completed")
