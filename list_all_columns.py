"""
List ALL columns in the unified_data_DataType_Raghu table
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def list_columns():
    """Get all column names from the table"""
    url = f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    # Get one record to see all columns
    params = {
        "limit": 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data and len(data) > 0:
            columns = list(data[0].keys())
            
            print("="*80)
            print(f"📋 ALL COLUMNS IN unified_data_DataType_Raghu ({len(columns)} total)")
            print("="*80)
            
            # Group by category
            location_cols = [c for c in columns if 'location' in c.lower() or 'lat' in c.lower() or 'lng' in c.lower() or 'long' in c.lower() or 'coord' in c.lower() or 'geom' in c.lower() or 'point' in c.lower()]
            google_cols = [c for c in columns if 'google' in c.lower() and c not in location_cols]
            other_cols = [c for c in columns if c not in location_cols and c not in google_cols]
            
            print("\n🗺️  LOCATION/COORDINATE COLUMNS:")
            for col in sorted(location_cols):
                print(f"   - {col}")
            
            print("\n🔍 GOOGLE-RELATED COLUMNS:")
            for col in sorted(google_cols):
                print(f"   - {col}")
            
            print(f"\n📦 OTHER COLUMNS ({len(other_cols)}):")
            for col in sorted(other_cols):
                print(f"   - {col}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    list_columns()
