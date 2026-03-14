import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Checking geom column in locations table...")

try:
    # Get a sample location to see what geom looks like
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/locations?select=id,name,geom&limit=3",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} locations")
        if len(data) > 0:
            for i, sample in enumerate(data):
                print(f"\nLocation {i+1}: {sample.get('name')}")
                print(f"  ID: {sample.get('id')}")
                print(f"  Geom value: {sample.get('geom')}")
                print(f"  Geom type: {type(sample.get('geom'))}")
                
                # Check if it's a WKT string like "POINT(78.38 17.44)"
                geom_val = sample.get('geom')
                if isinstance(geom_val, str) and geom_val.startswith('POINT('):
                    print("  ✅ Geom is stored as WKT string (POINT format)")
                    # Extract coordinates
                    coords = geom_val.replace('POINT(', '').replace(')', '').split()
                    if len(coords) == 2:
                        print(f"     Longitude: {coords[0]}")
                        print(f"     Latitude: {coords[1]}")
                else:
                    print("  ❓ Geom format is different")
        else:
            print("No data returned")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")