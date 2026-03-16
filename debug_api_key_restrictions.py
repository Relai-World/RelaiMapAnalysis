#!/usr/bin/env python3
"""
Debug API key restrictions by comparing working vs failing requests
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_with_different_user_agents():
    """Test with different User-Agent headers"""
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': '17.4436222,78.3519638',
        'radius': 5000,
        'type': 'hospital',
        'key': api_key
    }
    
    # Test different User-Agent headers
    user_agents = [
        "python-requests/2.31.0",  # Default requests user agent
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",  # Browser-like
        "uvicorn/0.24.0",  # Server-like
        "",  # No user agent
    ]
    
    for i, ua in enumerate(user_agents):
        print(f"\n🧪 Test {i+1}: User-Agent = '{ua}'")
        
        headers = {}
        if ua:
            headers['User-Agent'] = ua
            
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            
            if status == 'OK':
                results = data.get('results', [])
                print(f"✅ SUCCESS! Found {len(results)} results")
            else:
                error_msg = data.get('error_message', 'No error message')
                print(f"❌ FAILED: {status}")
                print(f"   Error: {error_msg[:100]}...")
                
        except Exception as e:
            print(f"🔥 Exception: {e}")

def test_with_referer_headers():
    """Test with different Referer headers"""
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': '17.4436222,78.3519638',
        'radius': 5000,
        'type': 'hospital',
        'key': api_key
    }
    
    # Test different Referer headers
    referers = [
        None,  # No referer
        "http://localhost:8000",
        "https://west-hyderabad-intelliweb.onrender.com",
        "http://127.0.0.1:8000",
    ]
    
    for i, referer in enumerate(referers):
        print(f"\n🧪 Test {i+1}: Referer = '{referer}'")
        
        headers = {}
        if referer:
            headers['Referer'] = referer
            
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            
            if status == 'OK':
                results = data.get('results', [])
                print(f"✅ SUCCESS! Found {len(results)} results")
            else:
                error_msg = data.get('error_message', 'No error message')
                print(f"❌ FAILED: {status}")
                print(f"   Error: {error_msg[:100]}...")
                
        except Exception as e:
            print(f"🔥 Exception: {e}")

def check_ip_restrictions():
    """Check if IP restrictions might be the issue"""
    print("\n🌐 IP Information:")
    try:
        # Get public IP
        ip_response = requests.get('https://api.ipify.org?format=json', timeout=5)
        public_ip = ip_response.json().get('ip', 'Unknown')
        print(f"   Public IP: {public_ip}")
        
        # Get local IP info
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   Local IP: {local_ip}")
        print(f"   Hostname: {hostname}")
        
    except Exception as e:
        print(f"   Could not get IP info: {e}")

if __name__ == "__main__":
    print("🔍 Debugging API Key Restrictions")
    print("=" * 50)
    
    check_ip_restrictions()
    test_with_different_user_agents()
    test_with_referer_headers()