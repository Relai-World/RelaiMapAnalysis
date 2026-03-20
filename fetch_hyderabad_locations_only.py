#!/usr/bin/env python3
"""
Fetch only Hyderabad location names from Supabase (filtering out Bangalore locations)
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def call_supabase_rpc(function_name, params=None):
    """Call a Supabase RPC function - same approach as frontend"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise Exception("Missing Supabase credentials in .env file")
    
    url = f"{supabase_url}/rest/v1/rpc/{function_name}"
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    body = params if params else {}
    
    print(f"🔍 Calling Supabase RPC: {function_name}")
    response = requests.post(url, headers=headers, json=body)
    
    print(f"🔍 Response status: {response.status_code}")
    
    if response.status_code != 200:
        error_text = response.text
        print(f"❌ Supabase RPC error: {response.status_code} - {error_text}")
        raise Exception(f"Supabase RPC error: {response.status_code} - {error_text}")
    
    data = response.json()
    print(f"✅ RPC {function_name} success")
    return data

def is_hyderabad_location(location_name, latitude, longitude):
    """Filter to identify Hyderabad locations based on coordinates and name patterns"""
    
    # Hyderabad coordinates range (approximate)
    # Latitude: 17.0° to 17.8° N
    # Longitude: 78.0° to 78.8° E
    
    # Bangalore coordinates range (approximate)  
    # Latitude: 12.7° to 13.2° N
    # Longitude: 77.3° to 77.9° E
    
    # Check coordinates first (most reliable)
    if latitude and longitude:
        # Hyderabad area
        if 17.0 <= latitude <= 17.8 and 78.0 <= longitude <= 78.8:
            return True
        # Bangalore area - exclude
        if 12.7 <= latitude <= 13.2 and 77.3 <= longitude <= 77.9:
            return False
    
    # Check for obvious Bangalore location names
    bangalore_keywords = [
        'bengaluru', 'bangalore', 'electronic city', 'whitefield', 'koramangala',
        'indiranagar', 'jp nagar', 'banashankari', 'jayanagar', 'malleshwaram',
        'rajajinagar', 'hebbal', 'marathahalli', 'bellandur', 'sarjapur',
        'hsr layout', 'btm layout', 'mg road', 'brigade road', 'commercial street'
    ]
    
    location_lower = location_name.lower()
    for keyword in bangalore_keywords:
        if keyword in location_lower:
            return False
    
    # Default to True for ambiguous cases (assume Hyderabad since it's the main focus)
    return True

def fetch_hyderabad_locations():
    """Fetch only Hyderabad location names using the get_all_insights RPC function"""
    try:
        print("🚀 Fetching location data using get_all_insights RPC...")
        
        # Use the same RPC function as the frontend
        insights_data = call_supabase_rpc('get_all_insights')
        
        if not insights_data:
            print("⚠️ No data returned from get_all_insights RPC")
            return []
        
        print(f"📊 Total insights data: {len(insights_data)} items")
        
        # Extract and filter Hyderabad locations
        hyderabad_locations = []
        bangalore_locations = []
        location_names = set()  # Use set to avoid duplicates
        
        for item in insights_data:
            if isinstance(item, dict):
                location_name = item.get('location')
                location_id = item.get('location_id')
                latitude = item.get('latitude')
                longitude = item.get('longitude')
                
                if location_name and location_name not in location_names:
                    location_names.add(location_name)
                    
                    if is_hyderabad_location(location_name, latitude, longitude):
                        hyderabad_locations.append({
                            'name': location_name,
                            'id': location_id,
                            'latitude': latitude,
                            'longitude': longitude
                        })
                    else:
                        bangalore_locations.append({
                            'name': location_name,
                            'id': location_id,
                            'latitude': latitude,
                            'longitude': longitude
                        })
        
        # Sort locations alphabetically
        hyderabad_locations.sort(key=lambda x: x['name'])
        bangalore_locations.sort(key=lambda x: x['name'])
        
        print(f"📍 Found {len(hyderabad_locations)} Hyderabad locations:")
        print(f"📍 Found {len(bangalore_locations)} Bangalore locations (filtered out)")
        print("=" * 60)
        
        for i, location in enumerate(hyderabad_locations, 1):
            location_id = location.get('id')
            name = location.get('name')
            lat = location.get('latitude')
            lng = location.get('longitude')
            print(f"{i:3d}. {name} (ID: {location_id}) [{lat:.4f}, {lng:.4f}]")
        
        print("=" * 60)
        print(f"Total Hyderabad locations: {len(hyderabad_locations)}")
        
        # Save Hyderabad locations to file
        with open('hyderabad_locations_only.txt', 'w', encoding='utf-8') as f:
            f.write(f"Hyderabad Locations Only ({len(hyderabad_locations)} total)\n")
            f.write("=" * 60 + "\n")
            for i, location in enumerate(hyderabad_locations, 1):
                location_id = location.get('id')
                name = location.get('name')
                lat = location.get('latitude')
                lng = location.get('longitude')
                f.write(f"{i:3d}. {name} (ID: {location_id}) [{lat:.4f}, {lng:.4f}]\n")
        
        # Also save filtered out Bangalore locations for reference
        with open('bangalore_locations_filtered.txt', 'w', encoding='utf-8') as f:
            f.write(f"Bangalore Locations (Filtered Out) ({len(bangalore_locations)} total)\n")
            f.write("=" * 60 + "\n")
            for i, location in enumerate(bangalore_locations, 1):
                location_id = location.get('id')
                name = location.get('name')
                lat = location.get('latitude')
                lng = location.get('longitude')
                f.write(f"{i:3d}. {name} (ID: {location_id}) [{lat:.4f}, {lng:.4f}]\n")
        
        print(f"✅ Hyderabad locations saved to 'hyderabad_locations_only.txt'")
        print(f"✅ Bangalore locations saved to 'bangalore_locations_filtered.txt'")
        
        return hyderabad_locations
        
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

if __name__ == "__main__":
    locations = fetch_hyderabad_locations()