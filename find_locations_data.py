#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def find_locations_data():
    """Find where location data is stored"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try different possible table names
        possible_tables = [
            'locations',
            'location',
            'news_balanced_corpus_1',  # This might have location data
            'unified_data_DataType_Raghu'  # Property data with locations
        ]
        
        print(f"🔍 SEARCHING FOR LOCATION DATA")
        print(f"=" * 50)
        
        for table_name in possible_tables:
            try:
                print(f"\nChecking table: {table_name}")
                response = supabase.table(table_name).select('*').limit(1).execute()
                
                if response.data:
                    print(f"✅ Found data in {table_name}")
                    print(f"   Columns: {list(response.data[0].keys())}")
                    
                    # Get count
                    count_response = supabase.table(table_name).select('*', count='exact').execute()
                    print(f"   Total records: {count_response.count}")
                    
                    # Look for location-related columns
                    location_columns = [col for col in response.data[0].keys() 
                                      if 'location' in col.lower() or 'area' in col.lower()]
                    if location_columns:
                        print(f"   Location columns: {location_columns}")
                        
                else:
                    print(f"❌ No data in {table_name}")
                    
            except Exception as e:
                print(f"❌ Error accessing {table_name}: {str(e)[:100]}...")
                
        # Also check the future development table to see what we have
        print(f"\n📊 FUTURE DEVELOPMENT SCRAPER DATA:")
        print(f"-" * 50)
        try:
            future_response = supabase.table('future_development_scrap').select('location_name').execute()
            unique_locations = list(set([r['location_name'] for r in future_response.data]))
            print(f"Unique locations in future_development_scrap: {len(unique_locations)}")
            print(f"Sample locations: {unique_locations[:10]}")
        except Exception as e:
            print(f"Error checking future_development_scrap: {e}")
            
    except Exception as e:
        print(f"❌ Error finding location data: {e}")

if __name__ == "__main__":
    find_locations_data()