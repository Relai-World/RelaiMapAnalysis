#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_all_locations_after_shamshabad():
    """Get ALL locations that come after Shamshabad alphabetically"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get all locations from RPC
        result = supabase.rpc('get_all_insights').execute()
        if result.data:
            # Filter by coordinates - Hyderabad is at ~17°N, 78°E
            hyderabad_locations = []
            
            for loc in result.data:
                lat = loc.get('latitude')
                lng = loc.get('longitude')
                
                # Check if coordinates are in Hyderabad range
                if lat and lng and (17.0 <= lat <= 18.0) and (78.0 <= lng <= 79.0):
                    hyderabad_locations.append((loc['location_id'], loc['location']))
            
            # Sort alphabetically
            hyderabad_locations.sort(key=lambda x: x[1].lower())
            
            print(f"📍 ALL HYDERABAD LOCATIONS (Alphabetically sorted):")
            print(f"=" * 60)
            
            shamshabad_index = -1
            for i, (loc_id, location) in enumerate(hyderabad_locations):
                status = ""
                if 'shamshabad' in location.lower():
                    shamshabad_index = i
                    status = " ← SHAMSHABAD (LAST SCRAPED)"
                elif i <= shamshabad_index:
                    status = " (already scraped)"
                elif i > shamshabad_index:
                    status = " (TO BE SCRAPED)"
                    
                print(f"{i+1:3d}. {location}{status}")
            
            if shamshabad_index == -1:
                print("⚠️ Shamshabad not found in the list!")
                return []
            
            # Return ALL locations after Shamshabad
            locations_after_shamshabad = hyderabad_locations[shamshabad_index + 1:]
            
            print(f"\n🎯 LOCATIONS TO SCRAPE AFTER SHAMSHABAD:")
            print(f"=" * 60)
            print(f"Total locations after Shamshabad: {len(locations_after_shamshabad)}")
            
            for i, (loc_id, location) in enumerate(locations_after_shamshabad, 1):
                print(f"{i:2d}. {location} (ID: {loc_id})")
            
            return locations_after_shamshabad
            
        else:
            print("⚠️ No locations found in Supabase")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching locations: {e}")
        return []

if __name__ == "__main__":
    locations = get_all_locations_after_shamshabad()