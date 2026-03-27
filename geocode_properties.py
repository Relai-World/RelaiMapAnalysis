"""
Geocode properties missing google_place_location using Google Places API
and update the Supabase database
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_properties_without_coords():
    """Fetch ALL properties where google_place_location is NULL"""
    url = f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    all_properties = []
    offset = 0
    limit = 1000
    
    print("🔍 Fetching properties without google_place_location...")
    
    while True:
        # Get properties where google_place_location is null
        params = {
            "select": "id,projectname,areaname,buildername",
            "google_place_location": "is.null",
            "limit": limit,
            "offset": offset
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            batch = response.json()
            
            if not batch:
                break
                
            all_properties.extend(batch)
            print(f"  📦 Fetched batch: {len(batch)} properties (total so far: {len(all_properties)})")
            
            if len(batch) < limit:
                break
                
            offset += limit
        else:
            print(f"❌ Error fetching properties: {response.status_code}")
            print(response.text)
            break
    
    print(f"✅ Found {len(all_properties)} properties without google_place_location\n")
    return all_properties

def geocode_address(address):
    """Geocode an address using Google Places API"""
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": address,
        "inputtype": "textquery",
        "fields": "geometry,formatted_address,name",
        "key": GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "OK" and len(data.get("candidates", [])) > 0:
            candidate = data["candidates"][0]
            location = candidate["geometry"]["location"]
            
            return {
                "lat": location["lat"],
                "lng": location["lng"]
            }
        else:
            print(f"  ⚠️ Geocoding failed: {data.get('status')}")
            return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def update_property_location(property_id, lat, lng):
    """Update property with geocoded location"""
    url = f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Store as JSON string
    location_json = f'{{"lat": {lat}, "lng": {lng}}}'
    
    update_data = {
        "google_place_location": location_json
    }
    
    params = {"id": f"eq.{property_id}"}
    
    response = requests.patch(url, headers=headers, params=params, json=update_data)
    
    return response.status_code in [200, 204]

def main():
    print("🚀 Starting geocoding process...")
    print(f"📍 Google API Key: {GOOGLE_API_KEY[:20]}...")
    print(f"🗄️ Supabase URL: {SUPABASE_URL}\n")
    
    properties = get_properties_without_coords()
    
    if not properties:
        print("✅ All properties already have coordinates!")
        return
    
    print(f"📝 Processing {len(properties)} properties...\n")
    
    # Cache coordinates by project+area to avoid duplicate API calls
    coords_cache = {}
    
    success_count = 0
    failed_count = 0
    cached_count = 0
    
    for i, prop in enumerate(properties, 1):
        prop_id = prop["id"]
        project_name = prop.get("projectname", "Unknown")
        area_name = prop.get("areaname", "")
        
        # Create cache key
        cache_key = f"{project_name}|{area_name}".lower()
        
        print(f"[{i}/{len(properties)}] {project_name} ({area_name})")
        
        # Check if we already geocoded this project+area
        if cache_key in coords_cache:
            location = coords_cache[cache_key]
            print(f"  🔄 Using cached: {location['lat']}, {location['lng']}")
            cached_count += 1
        else:
            # Build address
            address_parts = [project_name]
            if area_name:
                address_parts.append(area_name)
            address_parts.append("Hyderabad")
            address = ", ".join(address_parts)
            
            # Geocode
            location = geocode_address(address)
            
            if location:
                print(f"  ✅ Found: {location['lat']}, {location['lng']}")
                # Cache it for future units of same project
                coords_cache[cache_key] = location
            else:
                failed_count += 1
                continue
        
        # Update database
        if update_property_location(prop_id, location['lat'], location['lng']):
            success_count += 1
        else:
            print(f"  ❌ Update failed")
            failed_count += 1
        
        # Rate limiting (only if we made an API call)
        if cache_key not in coords_cache or i == 1:
            time.sleep(0.05)  # 50ms delay = 20 requests/second
    
    print("\n" + "="*60)
    print(f"✅ Successfully geocoded: {success_count}")
    print(f"🔄 Used cached coordinates: {cached_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total: {len(properties)}")
    print(f"🎯 Unique API calls: {len(coords_cache)}")
    print("="*60)

if __name__ == "__main__":
    main()
