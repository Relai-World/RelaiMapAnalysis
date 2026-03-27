"""
Verify that the Supabase function fix worked correctly
Run this after applying FIX_SUPABASE_FUNCTION.sql
"""
import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Testing Supabase function after fix...\n")

# Test 1: Call the function for Gachibowli
print("Test 1: Fetching Gachibowli properties")
print("-" * 50)
try:
    result = client.rpc('get_properties_func', {
        'area_name': 'Gachibowli',
        'bhk_filter': None
    }).execute()
    
    if result.data and len(result.data) > 0:
        print(f"✅ Function returned {len(result.data)} properties")
        
        # Check first property
        prop = result.data[0]
        print(f"\nFirst property: {prop.get('projectname')}")
        print(f"  - ID: {prop.get('id')}")
        print(f"  - Area: {prop.get('areaname')}")
        print(f"  - google_place_location: {prop.get('google_place_location', 'None')[:100]}...")
        
        # Try to extract coordinates
        loc_str = prop.get('google_place_location')
        if loc_str:
            try:
                if isinstance(loc_str, str) and loc_str.startswith('{'):
                    loc = json.loads(loc_str)
                    lat = loc.get('lat')
                    lng = loc.get('lng')
                    print(f"  - Extracted coordinates: lat={lat}, lng={lng}")
                    
                    if lat and lng:
                        print("  ✅ Coordinates are valid!")
                    else:
                        print("  ❌ Coordinates are missing!")
                else:
                    print(f"  ℹ️ Location format: {type(loc_str)}")
            except Exception as e:
                print(f"  ⚠️ Could not parse location: {e}")
        else:
            print("  ⚠️ No google_place_location field")
        
        # Check if latitude/longitude fields exist (they shouldn't)
        if 'latitude' in prop or 'longitude' in prop:
            print("\n  ❌ WARNING: latitude/longitude fields found in response!")
            print("     This means the broken function is still active.")
            print("     Please run FIX_SUPABASE_FUNCTION.sql again.")
        else:
            print("\n  ✅ No latitude/longitude fields (correct!)")
            
    else:
        print("❌ Function returned no data")
        
except Exception as e:
    print(f"❌ Error calling function: {e}")

print("\n" + "=" * 50)
print("\nTest 2: Check table structure")
print("-" * 50)

# Test 2: Check if latitude/longitude columns exist in table
try:
    result = client.table('unified_data_DataType_Raghu').select('*').limit(1).execute()
    
    if result.data and len(result.data) > 0:
        columns = list(result.data[0].keys())
        
        has_lat_lng = 'latitude' in columns and 'longitude' in columns
        has_google_place = 'google_place_location' in columns
        
        print(f"Total columns in table: {len(columns)}")
        print(f"  - Has 'latitude' column: {('latitude' in columns)}")
        print(f"  - Has 'longitude' column: {('longitude' in columns)}")
        print(f"  - Has 'google_place_location' column: {has_google_place}")
        
        if has_lat_lng:
            print("\n  ℹ️ Table has latitude/longitude columns")
            print("     (This is OK if they contain data)")
        
        if has_google_place:
            print("\n  ✅ Table has google_place_location column (correct!)")
        else:
            print("\n  ❌ Table missing google_place_location column!")
            
except Exception as e:
    print(f"❌ Error checking table: {e}")

print("\n" + "=" * 50)
print("\n📋 Summary:")
print("-" * 50)
print("If you see:")
print("  ✅ Function returns properties with google_place_location")
print("  ✅ No latitude/longitude fields in function response")
print("  ✅ Coordinates can be extracted from google_place_location")
print("\nThen the fix is working correctly! 🎉")
print("\nNext steps:")
print("  1. Deploy to Render (if not already deployed)")
print("  2. Test connectivity feature on live site")
print("  3. Verify GOOGLE_MAPS_API_KEY is set in Render environment")
