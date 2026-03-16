#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_locations_table():
    """Check the structure of the locations table"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get a sample record to see column names
        response = supabase.table('locations').select('*').limit(3).execute()
        
        if response.data:
            print(f"📋 LOCATIONS TABLE STRUCTURE")
            print(f"=" * 50)
            print(f"Available columns: {list(response.data[0].keys())}")
            
            print(f"\n📊 SAMPLE DATA:")
            print(f"-" * 50)
            for i, record in enumerate(response.data, 1):
                print(f"\nRecord {i}:")
                for key, value in record.items():
                    print(f"  {key}: {value}")
                    
            # Get total count
            count_response = supabase.table('locations').select('*', count='exact').execute()
            total_count = count_response.count
            print(f"\n📈 TOTAL LOCATIONS: {total_count}")
            
        else:
            print("No data found in locations table")
            
    except Exception as e:
        print(f"❌ Error checking locations table: {e}")

if __name__ == "__main__":
    check_locations_table()