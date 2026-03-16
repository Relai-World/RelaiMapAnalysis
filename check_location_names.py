#!/usr/bin/env python3
"""
Check if all locations are Hyderabad locations
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Checking location names in database:\n")

result = sb.rpc('get_all_insights').execute()
locations = result.data

print(f"Total locations: {len(locations)}")

# Bangalore location keywords
bangalore_keywords = ['bengaluru', 'bangalore', 'aerospace park', 'agara', 'agrahara', 'akshaya nagar']

# Separate Hyderabad and Bangalore locations
bangalore_locs = []
hyderabad_locs = []

for loc in locations:
    name_lower = loc['location'].lower()
    is_bangalore = any(keyword in name_lower for keyword in bangalore_keywords)
    
    if is_bangalore:
        bangalore_locs.append(loc)
    else:
        hyderabad_locs.append(loc)

print(f"\nHyderabad locations: {len(hyderabad_locs)}")
print(f"Bangalore locations: {len(bangalore_locs)}")

print(f"\nSample Bangalore locations:")
for loc in bangalore_locs[:5]:
    print(f"  - {loc['location']} (ID: {loc['location_id']})")

print(f"\nSample Hyderabad locations:")
for loc in hyderabad_locs[:5]:
    print(f"  - {loc['location']} (ID: {loc['location_id']})")
