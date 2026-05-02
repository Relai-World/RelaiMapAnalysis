"""
Count how many properties are missing coordinates
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def count_missing():
    """Count properties with and without coordinates"""
    url = f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "count=exact"
    }
    
    # Count total properties
    response = requests.get(url, headers=headers, params={"select": "id", "limit": 1})
    total = int(response.headers.get('Content-Range', '0-0/0').split('/')[1])
    
    # Count properties WITH coordinates
    response = requests.get(url, headers=headers, params={
        "select": "id",
        "google_place_location": "not.is.null",
        "limit": 1
    })
    with_coords = int(response.headers.get('Content-Range', '0-0/0').split('/')[1])
    
    # Count properties WITHOUT coordinates
    without_coords = total - with_coords
    
    print("="*60)
    print("📊 PROPERTY COORDINATES STATUS")
    print("="*60)
    print(f"Total properties:              {total:,}")
    print(f"✅ With coordinates:            {with_coords:,} ({with_coords/total*100:.1f}%)")
    print(f"❌ Missing coordinates:         {without_coords:,} ({without_coords/total*100:.1f}%)")
    print("="*60)
    
    if without_coords > 0:
        print("\n💡 SOLUTION:")
        print("Run the geocoding script to add coordinates:")
        print("  python geocode_properties.py")
        print("\nThis will use Google Places API to geocode missing properties.")

if __name__ == "__main__":
    count_missing()
