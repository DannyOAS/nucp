import requests
import json
from datetime import datetime

# Print header with timestamp
print(f"API Version Test - {datetime.now()}")

# Base URL of your API
base_url = "http://127.0.0.1:8000/api"

# Provider1's authentication token
auth_token = "3b640efbc529162d9c1645d96083dd7340c719ff"
auth_headers = {
    "Authorization": f"Token {auth_token}"
}

# Test the provider API endpoints
print("\n--- Testing Provider API (v1) ---")
provider_endpoints = [
    "/v1/provider/profile/",
    "/v1/provider/appointments/",
    "/v1/provider/prescriptions/",
    "/v1/provider/patients/",
    "/v1/provider/messages/"
]

for endpoint in provider_endpoints:
    try:
        full_url = f"{base_url}{endpoint}"
        print(f"\nTesting: {full_url}")
        
        response = requests.get(full_url, headers=auth_headers)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} Status: {response.status_code}")
        
        # Check for version info in the response
        if response.status_code == 200:
            data = response.json()
            
            # Print a sample of the response
            print("Response preview:")
            if isinstance(data, list):
                if data:  # If the list has items
                    sample = data[0]
                    print(json.dumps(sample, indent=2)[:500] + "..." if len(json.dumps(sample)) > 500 else json.dumps(sample, indent=2))
                else:
                    print("(Empty list)")
            else:
                preview = json.dumps(data, indent=2)
                print(preview[:500] + "..." if len(preview) > 500 else preview)
            
            # Check for api_version in both top-level and nested results
            version_found = False
            
            # Check top level
            if isinstance(data, dict) and 'api_version' in data:
                print(f"✅ Version info found at top level: {data['api_version']}")
                version_found = True
            
            # Check in results if paginated response
            if isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
                if data['results'] and isinstance(data['results'][0], dict) and 'api_version' in data['results'][0]:
                    print(f"✅ Version info found in results items: {data['results'][0]['api_version']}")
                    version_found = True
            
            # Check list items directly if not paginated
            elif isinstance(data, list) and data and isinstance(data[0], dict) and 'api_version' in data[0]:
                print(f"✅ Version info found in list items: {data[0]['api_version']}")
                version_found = True
            
            if not version_found:
                print("❌ Version info not found in response")
                # Print the keys to see what's in the response
                if isinstance(data, dict):
                    print(f"Available keys: {list(data.keys())}")
                    
                    # If paginated, check the structure of a result item
                    if 'results' in data and data['results'] and isinstance(data['results'][0], dict):
                        print(f"Result item keys: {list(data['results'][0].keys())}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Test legacy API redirects
print("\n--- Testing Legacy API Redirects ---")
legacy_endpoints = [
    "/provider/profile/", 
    "/provider/appointments/"
]

for endpoint in legacy_endpoints:
    try:
        full_url = f"{base_url}{endpoint}"
        print(f"\nTesting redirect: {full_url}")
        
        # Use allow_redirects=False to see the redirect status without following it
        response = requests.get(full_url, headers=auth_headers, allow_redirects=False)
        
        if response.status_code in (301, 302, 307, 308):  # All redirect status codes
            location = response.headers.get('Location', '')
            status = "✅" if "/v1/" in location else "❌"
            print(f"{status} Redirects properly - Status: {response.status_code}")
            print(f"Redirect target: {location}")
            
            # Optionally follow the redirect and check the final destination
            print("\nFollowing redirect to check destination...")
            redirect_response = requests.get(full_url, headers=auth_headers)
            if redirect_response.status_code == 200:
                print(f"✅ Redirect destination responds with 200 OK")
                
                # Check if version info exists in the redirect destination
                try:
                    redirect_data = redirect_response.json()
                    if isinstance(redirect_data, dict) and 'api_version' in redirect_data:
                        print(f"✅ Version info found in redirect destination: {redirect_data['api_version']}")
                    else:
                        print("❌ Version info not found in redirect destination")
                except:
                    print("❌ Could not parse JSON from redirect destination")
            else:
                print(f"❌ Redirect destination returned status: {redirect_response.status_code}")
        else:
            print(f"❌ Status: {response.status_code} (expected 301 or 302)")
            
            # Print response content to help debug
            print(f"Response body: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\nTests completed")
