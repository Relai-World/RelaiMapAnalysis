#!/usr/bin/env python3
"""
Check location table structure and find Hyderabad locations properly
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Checking location data structure:\n")

# Get insights data
result = sb.rpc('get_all_insights').execute()
locations = result.data

if locations:
    print("Sample location data structure:")
    print(f"Keys: {list(locations[0].keys())}\n")
    
    print("First 3 locations:")
    for loc in locations[:3]:
        print(f"  ID: {loc['location_id']}, Name: {loc['location']}")
        # Check if there are any other fields that indicate city/region
        for key, value in loc.items():
            if key not in ['location_id', 'location', 'longitude', 'latitude', 'avg_sentiment', 'growth_score', 'investment_score']:
                print(f"    {key}: {value}")

# Check if there's a region or city field
print("\n" + "="*70)
print("Analyzing location names for patterns:")
print("="*70)

# Look for patterns
west_hyd = [loc for loc in locations if 'west' in loc['location'].lower()]
print(f"\nLocations with 'west': {len(west_hyd)}")
if west_hyd:
    for loc in west_hyd[:3]:
        print(f"  - {loc['location']}")

# Check coordinates to determine Hyderabad vs Bangalore
# Hyderabad: ~17.4°N, 78.5°E
# Bangalore: ~12.9°N, 77.6°E

hyd_locs = []
blr_locs = []
unknown_locs = []

for loc in locations:
    lat = loc.get('latitude')
    lng = loc.get('longitude')
    
    if lat and lng:
        # Hyderabad coordinates range
        if 17.0 <= lat <= 18.0 and 78.0 <= lng <= 79.0:
            hyd_locs.append(loc)
        # Bangalore coordinates range
        elif 12.5 <= lat <= 13.5 and 77.0 <= lng <= 78.0:
            blr_locs.append(loc)
        else:
            unknown_locs.append(loc)
    else:
        unknown_locs.append(loc)

print(f"\n" + "="*70)
print("LOCATION BREAKDOWN BY COORDINATES:")
print("="*70)
print(f"Hyderabad (17°N, 78°E): {len(hyd_locs)} locations")
print(f"Bangalore (12.9°N, 77.6°E): {len(blr_locs)} locations")
print(f"Unknown/No coordinates: {len(unknown_locs)} locations")

print(f"\nSample Hyderabad locations:")
for loc in hyd_locs[:5]:
    print(f"  - {loc['location']} ({loc['latitude']:.2f}, {loc['longitude']:.2f})")

print(f"\nSample Bangalore locations:")
for loc in blr_locs[:5]:
    print(f"  - {loc['location']} ({loc['latitude']:.2f}, {loc['longitude']:.2f})")
