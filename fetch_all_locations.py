#!/usr/bin/env python3
"""
Fetch all location names from Supabase using the same RPC function as the frontend
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

def fetch_all_locations():
    """Fetch all location names using the get_all_insights RPC function (same as frontend)"""
    try:
        print("🚀 Fetching location data using get_all_insights RPC...")
        
        # Use the same RPC function as the frontend
        insights_data = call_supabase_rpc('get_all_insights')
        
        if not insights_data:
            print("⚠️ No data returned from get_all_insights RPC")
            return []
        
        print(f"📊 Raw insights data type: {type(insights_data)}")
        print(f"📊 Raw insights data length: {len(insights_data) if isinstance(insights_data, list) else 'Not a list'}")
        
        # Let's examine the first few items to understand the structure
        if isinstance(insights_data, list) and len(insights_data) > 0:
            print("🔍 Examining first few items to understand data structure:")
            for i, item in enumerate(insights_data[:3]):
                print(f"Item {i+1}: {item}")
                if isinstance(item, dict):
                    print(f"  Keys: {list(item.keys())}")
        
        # Extract location names from the insights data
        locations = []
        location_names = set()  # Use set to avoid duplicates
        
        for item in insights_data:
            if isinstance(item, dict):
                # Check all possible location name fields
                location_name = None
                location_id = None
                
                # Try different possible field names
                for field in ['location_name', 'name', 'area_name', 'location', 'area']:
                    if field in item and item[field]:
                        location_name = item[field]
                        break
                
                # Try different possible ID fields
                for field in ['location_id', 'id', 'area_id']:
                    if field in item and item[field]:
                        location_id = item[field]
                        break
                
                if location_name and location_name not in location_names:
                    location_names.add(location_name)
                    locations.append({
                        'name': location_name,
                        'id': location_id if location_id else 'N/A'
                    })
        
        # Sort locations alphabetically
        locations.sort(key=lambda x: x['name'])
        
        print(f"📍 Found {len(locations)} unique locations in Hyderabad:")
        print("=" * 60)
        
        for i, location in enumerate(locations, 1):
            location_id = location.get('id')
            name = location.get('name')
            print(f"{i:3d}. {name} (ID: {location_id})")
        
        print("=" * 60)
        print(f"Total: {len(locations)} locations")
        
        # Also save to a text file
        with open('hyderabad_locations.txt', 'w', encoding='utf-8') as f:
            f.write(f"Hyderabad Locations ({len(locations)} total)\n")
            f.write("=" * 60 + "\n")
            for i, location in enumerate(locations, 1):
                location_id = location.get('id')
                name = location.get('name')
                f.write(f"{i:3d}. {name} (ID: {location_id})\n")
        
        print(f"✅ Location list saved to 'hyderabad_locations.txt'")
        
        return locations
        
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

if __name__ == "__main__":
    locations = fetch_all_locations()