#!/usr/bin/env python3
"""
Debug the future development frontend issue
"""

import requests
import json

def test_api_endpoints():
    """Test various API endpoints to see which ones work"""
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        "/",
        "/api/v1/insights", 
        "/api/v1/future-development/1",
        "/api/v1/future-development/35",  # Abids - we know has data
        "/api/v1/search?q=gachibowli"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🔍 Testing: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if endpoint.startswith("/api/v1/future-development"):
                        print(f"Success: {data.get('success', 'N/A')}")
                        print(f"Total: {data.get('total_count', 'N/A')}")
                        if data.get('developments'):
                            print(f"First dev: {data['developments'][0].get('source', 'N/A')}")
                    else:
                        print(f"Response type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"Keys: {list(data.keys())[:5]}")
                        elif isinstance(data, list):
                            print(f"List length: {len(data)}")
                except:
                    print(f"Response text: {response.text[:100]}...")
            else:
                print(f"Error: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error - API server not running?")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def check_frontend_url():
    """Check what URL the frontend would actually call"""
    
    # Simulate what the frontend does
    location_id = 35  # Abids
    frontend_url = f"/api/v1/future-development/{location_id}"
    
    print(f"\n🌐 Frontend would call: {frontend_url}")
    print("This should match the FastAPI route: @app.get('/api/v1/future-development/{location_id}')")

if __name__ == "__main__":
    print("🚀 Debugging Future Development API...")
    test_api_endpoints()
    check_frontend_url()