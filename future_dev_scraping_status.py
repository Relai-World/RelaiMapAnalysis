#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def analyze_future_dev_scraping_status():
    """Analyze the complete status of future development scraping"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get all Hyderabad locations
        result = supabase.rpc('get_all_insights').execute()
        if not result.data:
            print("❌ No locations found")
            return
            
        # Filter Hyderabad locations (17°N, 78°E)
        hyderabad_locations = []
        for loc in result.data:
            lat = loc.get('latitude')
            lng = loc.get('longitude')
            if lat and lng and (17.0 <= lat <= 18.0) and (78.0 <= lng <= 79.0):
                hyderabad_locations.append((loc['location_id'], loc['location']))
        
        # Sort alphabetically
        hyderabad_locations.sort(key=lambda x: x[1].lower())
        
        # Get scraped locations from future_development_scrap
        scraped_response = supabase.table('future_development_scrap').select('location_name').execute()
        scraped_locations = set([loc['location_name'] for loc in scraped_response.data])
        
        # Find Shamshabad position
        shamshabad_index = -1
        for i, (loc_id, location) in enumerate(hyderabad_locations):
            if 'shamshabad' in location.lower():
                shamshabad_index = i
                break
        
        print(f"📊 FUTURE DEVELOPMENT SCRAPING STATUS")
        print(f"=" * 60)
        print(f"Total Hyderabad locations: {len(hyderabad_locations)}")
        print(f"Shamshabad position: {shamshabad_index + 1} of {len(hyderabad_locations)}")
        print(f"Locations scraped: {len(scraped_locations)}")
        print(f"Coverage: {len(scraped_locations)}/{len(hyderabad_locations)} ({(len(scraped_locations)/len(hyderabad_locations)*100):.1f}%)")
        
        # Analyze what's been scraped
        scraped_count = 0
        not_scraped_count = 0
        locations_up_to_shamshabad = 0
        locations_after_shamshabad = 0
        
        print(f"\n📋 DETAILED BREAKDOWN:")
        print(f"-" * 60)
        
        for i, (loc_id, location) in enumerate(hyderabad_locations):
            is_scraped = location in scraped_locations
            
            if i <= shamshabad_index:  # Up to and including Shamshabad
                locations_up_to_shamshabad += 1
                if is_scraped:
                    scraped_count += 1
                else:
                    not_scraped_count += 1
            else:  # After Shamshabad
                locations_after_shamshabad += 1
                if is_scraped:
                    scraped_count += 1
                else:
                    not_scraped_count += 1
        
        print(f"Locations up to Shamshabad (inclusive): {locations_up_to_shamshabad}")
        print(f"Locations after Shamshabad: {locations_after_shamshabad}")
        
        # Show what's missing up to Shamshabad
        missing_up_to_shamshabad = []
        missing_after_shamshabad = []
        
        for i, (loc_id, location) in enumerate(hyderabad_locations):
            if location not in scraped_locations:
                if i <= shamshabad_index:
                    missing_up_to_shamshabad.append(location)
                else:
                    missing_after_shamshabad.append(location)
        
        print(f"\n❌ MISSING LOCATIONS UP TO SHAMSHABAD ({len(missing_up_to_shamshabad)}):")
        print(f"-" * 60)
        for i, location in enumerate(missing_up_to_shamshabad, 1):
            print(f"{i:2d}. {location}")
        
        print(f"\n⏳ LOCATIONS AFTER SHAMSHABAD ({len(missing_after_shamshabad)}):")
        print(f"-" * 60)
        for i, location in enumerate(missing_after_shamshabad, 1):
            print(f"{i:2d}. {location}")
        
        print(f"\n🎯 SUMMARY:")
        print(f"-" * 60)
        print(f"Total locations: {len(hyderabad_locations)}")
        print(f"Already scraped: {len(scraped_locations)}")
        print(f"Missing up to Shamshabad: {len(missing_up_to_shamshabad)}")
        print(f"Remaining after Shamshabad: {len(missing_after_shamshabad)}")
        print(f"Total remaining to scrape: {len(missing_up_to_shamshabad) + len(missing_after_shamshabad)}")
        
        return {
            'total_locations': len(hyderabad_locations),
            'scraped_count': len(scraped_locations),
            'missing_up_to_shamshabad': missing_up_to_shamshabad,
            'missing_after_shamshabad': missing_after_shamshabad
        }
        
    except Exception as e:
        print(f"❌ Error analyzing scraping status: {e}")
        return None

if __name__ == "__main__":
    analyze_future_dev_scraping_status()