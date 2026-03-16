#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_future_dev_count():
    """Check how many locations were scraped in future_development_scrap table"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get total count
        response = supabase.table('future_development_scrap').select('*', count='exact').execute()
        total_count = response.count
        
        print(f"🏗️ FUTURE DEVELOPMENT SCRAPER RESULTS")
        print(f"=" * 50)
        print(f"Total locations scraped: {total_count}")
        
        if total_count > 0:
            # Get sample records to verify data quality
            sample_response = supabase.table('future_development_scrap').select('*').limit(5).execute()
            sample_data = sample_response.data
            
            print(f"\n📊 SAMPLE DATA (First 5 records):")
            print(f"-" * 50)
            
            for i, record in enumerate(sample_data, 1):
                print(f"\n{i}. Location: {record.get('location_name', 'N/A')}")
                print(f"   Coordinates: ({record.get('latitude', 'N/A')}, {record.get('longitude', 'N/A')})")
                print(f"   Expected Completion: {record.get('expected_completion_year', 'N/A')}")
                print(f"   Project Type: {record.get('project_type', 'N/A')}")
                print(f"   Description: {record.get('description', 'N/A')[:100]}...")
            
            # Check location distribution
            location_response = supabase.table('future_development_scrap').select('location_name').execute()
            locations = [r['location_name'] for r in location_response.data if r.get('location_name')]
            unique_locations = set(locations)
            
            print(f"\n🗺️ LOCATION COVERAGE:")
            print(f"-" * 50)
            print(f"Unique locations covered: {len(unique_locations)}")
            print(f"Total records: {len(locations)}")
            print(f"Average records per location: {len(locations) / len(unique_locations):.1f}")
            
            # Show top 10 locations by record count
            from collections import Counter
            location_counts = Counter(locations)
            top_locations = location_counts.most_common(10)
            
            print(f"\n🏆 TOP 10 LOCATIONS BY PROJECT COUNT:")
            print(f"-" * 50)
            for location, count in top_locations:
                print(f"   {location}: {count} projects")
                
        else:
            print("\n❌ No data found in future_development_scrap table")
            print("   The scraper may not have run yet or encountered issues")
            
    except Exception as e:
        print(f"❌ Error checking future development data: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_future_dev_count()