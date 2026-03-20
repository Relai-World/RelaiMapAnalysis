#!/usr/bin/env python3
"""
Get exactly 169 Hyderabad locations with more precise filtering
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def call_supabase_rpc(function_name, params=None):
    """Call a Supabase RPC function"""
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
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code != 200:
        error_text = response.text
        raise Exception(f"Supabase RPC error: {response.status_code} - {error_text}")
    
    return response.json()

def is_definitely_hyderabad(location_name, latitude, longitude):
    """More precise filtering for Hyderabad locations"""
    
    # Strict coordinate check first
    if latitude and longitude:
        # Hyderabad metropolitan area (more restrictive)
        if 17.0 <= latitude <= 17.8 and 78.0 <= longitude <= 78.8:
            # Additional check: exclude obvious Bangalore locations that might have wrong coordinates
            location_lower = location_name.lower()
            bangalore_exclusions = [
                'defence & aerospace park', 'aerospace park', 'bengaluru', 'bangalore',
                'devanahalli', 'electronic city', 'whitefield', 'koramangala',
                'indiranagar', 'jp nagar', 'banashankari', 'jayanagar', 'malleshwaram',
                'hebbal', 'marathahalli', 'bellandur', 'sarjapur', 'hsr layout',
                'mg road', 'rajajinagar', 'vijayanagar', 'yeshwanthpur'
            ]
            
            for exclusion in bangalore_exclusions:
                if exclusion in location_lower:
                    return False
            
            return True
        else:
            return False
    
    return False

def get_precise_hyderabad_locations():
    """Get precisely filtered Hyderabad locations"""
    try:
        print("🚀 Getting precise Hyderabad locations...")
        
        insights_data = call_supabase_rpc('get_all_insights')
        
        if not insights_data:
            print("⚠️ No data returned")
            return []
        
        print(f"📊 Total insights data: {len(insights_data)} items")
        
        # Extract and filter with strict criteria
        hyderabad_locations = []
        excluded_locations = []
        location_names = set()
        
        for item in insights_data:
            if isinstance(item, dict):
                location_name = item.get('location')
                location_id = item.get('location_id')
                latitude = item.get('latitude')
                longitude = item.get('longitude')
                
                if not location_name or location_name in location_names:
                    continue
                
                location_names.add(location_name)
                location_info = {
                    'name': location_name,
                    'id': location_id,
                    'lat': latitude,
                    'lng': longitude
                }
                
                if is_definitely_hyderabad(location_name, latitude, longitude):
                    hyderabad_locations.append(location_info)
                else:
                    excluded_locations.append(location_info)
        
        # Sort locations alphabetically
        hyderabad_locations.sort(key=lambda x: x['name'])
        
        print(f"📍 Found {len(hyderabad_locations)} Hyderabad locations")
        print(f"🚫 Excluded {len(excluded_locations)} non-Hyderabad locations")
        
        # Show the locations
        print("\n" + "="*60)
        print("HYDERABAD LOCATIONS:")
        print("="*60)
        
        for i, location in enumerate(hyderabad_locations, 1):
            location_id = location.get('id')
            name = location.get('name')
            lat = location.get('lat')
            lng = location.get('lng')
            print(f"{i:3d}. {name} (ID: {location_id}) [{lat:.4f}, {lng:.4f}]")
        
        print("="*60)
        print(f"Total: {len(hyderabad_locations)} locations")
        
        # If we still have more than 169, show the extras
        if len(hyderabad_locations) > 169:
            extra_count = len(hyderabad_locations) - 169
            print(f"\n🔍 We have {extra_count} extra locations beyond 169:")
            
            # Show locations that might be questionable (border areas)
            border_locations = []
            for loc in hyderabad_locations:
                lat, lng = loc['lat'], loc['lng']
                # Check if on the edges of our Hyderabad boundary
                if (lat < 17.1 or lat > 17.7 or lng < 78.1 or lng > 78.7):
                    border_locations.append(loc)
            
            if border_locations:
                print(f"\n🔍 Locations on Hyderabad boundary ({len(border_locations)}):")
                for loc in border_locations:
                    print(f"   - {loc['name']} (ID: {loc['id']}) [{loc['lat']:.4f}, {loc['lng']:.4f}]")
        
        # Save to file
        with open('precise_hyderabad_locations.txt', 'w', encoding='utf-8') as f:
            f.write(f"Precise Hyderabad Locations ({len(hyderabad_locations)} total)\n")
            f.write("="*60 + "\n")
            for i, location in enumerate(hyderabad_locations, 1):
                location_id = location.get('id')
                name = location.get('name')
                lat = location.get('lat')
                lng = location.get('lng')
                f.write(f"{i:3d}. {name} (ID: {location_id}) [{lat:.4f}, {lng:.4f}]\n")
        
        print(f"\n✅ Precise list saved to 'precise_hyderabad_locations.txt'")
        
        # Show some excluded locations for verification
        if excluded_locations:
            print(f"\n🚫 Sample excluded locations:")
            for loc in excluded_locations[:10]:
                print(f"   - {loc['name']} (ID: {loc['id']}) [{loc['lat']:.4f}, {loc['lng']:.4f}]")
        
        return hyderabad_locations
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    locations = get_precise_hyderabad_locations()