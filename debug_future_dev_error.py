#!/usr/bin/env python3

import requests
import json

def debug_future_dev_error():
    """Debug the exact future development API error"""
    
    print("🔍 DEBUGGING FUTURE DEVELOPMENT API ERROR")
    print("=" * 60)
    
    # Test the exact location IDs from the console error
    test_locations = [1, 35]
    
    for location_id in test_locations:
        print(f"\n📍 Testing Location ID: {location_id}")
        print("-" * 40)
        
        try:
            url = f"http://localhost:8000/api/v1/future-development/{location_id}"
            print(f"URL: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            # Check if response is HTML (error page) or JSON
            content = response.text
            print(f"Response Length: {len(content)} characters")
            
            if content.startswith('<!DOCTYPE') or content.startswith('<html'):
                print("❌ PROBLEM: API returned HTML instead of JSON")
                print("First 200 characters of response:")
                print(content[:200])
                print("...")
            else:
                print("✅ Response appears to be JSON")
                try:
                    data = response.json()
                    print(f"Success: {data.get('success', 'Unknown')}")
                    print(f"Total Count: {data.get('total_count', 'Unknown')}")
                    if data.get('error'):
                        print(f"API Error: {data['error']}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error: {e}")
                    print("Raw response:")
                    print(content[:500])
                    
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR: API server is not running!")
            print("Make sure to start the API server with: uvicorn api:app --reload")
            break
        except Exception as e:
            print(f"❌ Request Error: {e}")
    
    print(f"\n🔧 TROUBLESHOOTING STEPS:")
    print("-" * 40)
    print("1. Check if API server is running: http://localhost:8000/docs")
    print("2. Check if future_development_scrap table has data for these locations")
    print("3. Check API server logs for errors")
    print("4. Verify Supabase connection in API")

if __name__ == "__main__":
    debug_future_dev_error()