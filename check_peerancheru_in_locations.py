#!/usr/bin/env python3
"""
Check what Peerancheru-related locations exist in the locations table
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("CHECKING LOCATIONS TABLE FOR PEERANCHERU")
print("="*70)

# Get all insights to see location names
result = sb.rpc('get_all_insights').execute()

if result.data:
    # Filter for Peerancheru-related locations
    peerancheru_locs = [loc for loc in result.data if 'peer' in loc['location'].lower() or 'patan' in loc['location'].lower()]
    
    if peerancheru_locs:
        print(f"\nFound {len(peerancheru_locs)} Peerancheru-related locations:")
        for loc in peerancheru_locs:
            print(f"\n   Location: {loc['location']}")
            print(f"   ID: {loc['location_id']}")
            print(f"   Coordinates: ({loc['latitude']}, {loc['longitude']})")
            print(f"   Properties: {loc.get('property_count', 0)}")
    else:
        print("\n❌ NO Peerancheru-related locations found in locations table")
        print("\n💡 This explains why clicking on the map shows 0 properties!")
        print("   The location doesn't exist in the locations table.")

print("\n" + "="*70)
print("PROPERTY DATA SUMMARY:")
print("="*70)
print("Properties exist with these area names:")
print("   - Patancheru: 49 properties")
print("   - Patancheruvu: 166 properties")
print("   - Peeramcheruvu: 10 properties")
print("   - Peeranchuruvu: 8 properties")
print("   - Peerzadiguda: 97 properties")
print("   - Appa Junction Peerancheru: 4 properties")
print("\n💡 SOLUTION: Add these as locations in the locations table")
