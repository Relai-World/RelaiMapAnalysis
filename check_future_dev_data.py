#!/usr/bin/env python3
"""
Check what data exists in the future_development_scrap table
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_future_dev_data():
    """Check the future development data in Supabase"""
    
    try:
        # Initialize Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")  # Changed from SUPABASE_ANON_KEY
        
        if not url or not key:
            print("❌ Missing Supabase credentials in .env file")
            return
            
        supabase: Client = create_client(url, key)
        
        # Check if table exists and get sample data
        print("🔍 Checking future_development_scrap table...")
        
        # Get total count
        count_response = supabase.table('future_development_scrap').select('id', count='exact').execute()
        total_count = count_response.count
        print(f"📊 Total records: {total_count}")
        
        if total_count > 0:
            # Get sample records
            sample_response = supabase.table('future_development_scrap').select(
                'id, location_id, location_name, source, content, published_at, year_mentioned'
            ).limit(5).execute()
            
            print("\n📋 Sample records:")
            for i, record in enumerate(sample_response.data, 1):
                print(f"\n--- Record {i} ---")
                print(f"ID: {record.get('id')}")
                print(f"Location ID: {record.get('location_id')}")
                print(f"Location Name: {record.get('location_name')}")
                print(f"Source: {record.get('source')}")
                print(f"Year: {record.get('year_mentioned')}")
                print(f"Content: {record.get('content', '')[:100]}...")
                
            # Check unique location IDs
            locations_response = supabase.table('future_development_scrap').select(
                'location_id, location_name'
            ).execute()
            
            unique_locations = {}
            for record in locations_response.data:
                loc_id = record.get('location_id')
                loc_name = record.get('location_name')
                if loc_id:
                    unique_locations[loc_id] = loc_name
                    
            print(f"\n🗺️ Locations with future development data ({len(unique_locations)}):")
            for loc_id, loc_name in list(unique_locations.items())[:10]:
                print(f"  - ID {loc_id}: {loc_name}")
                
        else:
            print("⚠️ No data found in future_development_scrap table")
            print("💡 You may need to run the scraper to populate this table")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_future_dev_data()