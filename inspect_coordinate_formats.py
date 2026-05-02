"""
Inspect the actual format of coordinates in the database
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def inspect_formats():
    """Check the actual raw format of google_place_location"""
    url = f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    # Get properties with coordinates
    params = {
        "select": "id,projectname,buildername,areaname,google_place_location",
        "google_place_location": "not.is.null",
        "limit": 10
    }
    
    response = requests.get(url, headers=headers, params=params)
    properties = response.json()
    
    print("="*80)
    print("🔍 INSPECTING COORDINATE FORMATS IN DATABASE")
    print("="*80)
    
    for i, prop in enumerate(properties, 1):
        print(f"\n{i}. {prop['projectname']}")
        print(f"   Builder: {prop['buildername']}")
        print(f"   Area: {prop['areaname']}")
        
        loc = prop.get('google_place_location')
        
        print(f"\n   📦 Raw value type: {type(loc)}")
        print(f"   📦 Raw value: {repr(loc)[:200]}")
        
        # If it's a dict (JSONB), show the keys
        if isinstance(loc, dict):
            print(f"   🔑 Keys: {list(loc.keys())}")
            print(f"   📍 Values: {loc}")
        
        # If it's a string, try to parse it
        elif isinstance(loc, str):
            print(f"   📝 String length: {len(loc)}")
            
            # Try JSON parse
            try:
                parsed = json.loads(loc)
                print(f"   ✅ JSON parseable!")
                print(f"   🔑 Parsed keys: {list(parsed.keys())}")
                print(f"   📍 Parsed values: {parsed}")
            except json.JSONDecodeError as e:
                print(f"   ❌ Not valid JSON: {e}")
                
                # Check if it's a POINT format
                if 'POINT' in loc:
                    print(f"   🗺️  Looks like PostGIS POINT format")
        
        print("-" * 80)

if __name__ == "__main__":
    inspect_formats()
