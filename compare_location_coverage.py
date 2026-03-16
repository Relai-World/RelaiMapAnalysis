#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def compare_location_coverage():
    """Compare total locations vs future development scraper coverage"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get total unique locations from property data (areaname column)
        properties_response = supabase.table('unified_data_DataType_Raghu').select('areaname').execute()
        all_area_names = [prop['areaname'] for prop in properties_response.data if prop.get('areaname')]
        unique_locations = list(set(all_area_names))
        total_locations = len(unique_locations)
        
        # Get locations covered by future development scraper
        future_dev_response = supabase.table('future_development_scrap').select('location_name').execute()
        scraped_locations = list(set([loc['location_name'] for loc in future_dev_response.data]))
        scraped_count = len(scraped_locations)
        
        print(f"📍 LOCATION COVERAGE COMPARISON")
        print(f"=" * 60)
        print(f"Total unique locations in property data: {total_locations}")
        print(f"Locations covered by future dev scraper: {scraped_count}")
        print(f"Coverage percentage: {(scraped_count / total_locations) * 100:.1f}%")
        print(f"Missing locations: {total_locations - scraped_count}")
        
        # Find which locations are missing
        missing_locations = []
        for location in unique_locations:
            if location not in scraped_locations:
                missing_locations.append(location)
        
        print(f"\n🔍 MISSING LOCATIONS (First 30):")
        print(f"-" * 60)
        for i, location in enumerate(missing_locations[:30], 1):
            print(f"{i:2d}. {location}")
            
        if len(missing_locations) > 30:
            print(f"... and {len(missing_locations) - 30} more locations")
            
        # Show some covered locations for comparison
        print(f"\n✅ COVERED LOCATIONS (Sample 15):")
        print(f"-" * 60)
        for i, location in enumerate(scraped_locations[:15], 1):
            print(f"{i:2d}. {location}")
            
        # Check if we need to run the scraper for more locations
        if missing_locations:
            print(f"\n💡 RECOMMENDATION:")
            print(f"-" * 60)
            print(f"The future development scraper should be run for the remaining")
            print(f"{len(missing_locations)} locations to achieve full coverage.")
            print(f"Current coverage: {scraped_count}/{total_locations} locations")
            
            # Show top missing locations by property count
            from collections import Counter
            location_counts = Counter(all_area_names)
            missing_with_counts = [(loc, location_counts[loc]) for loc in missing_locations]
            missing_with_counts.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n🏆 TOP 15 MISSING LOCATIONS BY PROPERTY COUNT:")
            print(f"-" * 60)
            for location, count in missing_with_counts[:15]:
                print(f"   {location}: {count} properties")
            
        return missing_locations
            
    except Exception as e:
        print(f"❌ Error comparing location coverage: {e}")
        return []

if __name__ == "__main__":
    missing = compare_location_coverage()