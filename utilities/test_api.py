import requests

# Test the location costs API endpoint
url = "http://127.0.0.1:8000/api/v1/location-costs/Gachibowli"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
