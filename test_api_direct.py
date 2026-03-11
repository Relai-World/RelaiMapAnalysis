"""
Test API directly to see if changes are loaded
"""

import requests

# Test the API endpoint with debug info
base_url = "http://localhost:8000"

print("Testing API endpoint directly...")

try:
    # Test with BHK parameter
    response = requests.get(f"{base_url}/api/v1/properties?area=Hitec City&bhk=2")
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        properties = response.json()
        print(f"Response length: {len(properties)}")
        if properties:
            print(f"First property BHK: {properties[0].get('bhk')}")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Connection error: {e}")
    print("API server might not be running or changes not loaded")