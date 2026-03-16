#!/usr/bin/env python3
"""
Debug why Peerancheru doesn't show property data
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("DEBUGGING PEERANCHERU PROPERTY DATA ISSUE")
print("="*70)

# Step 1: Check if Peerancheru exists in locations table
print("\n1. Checking locations table for 'Peerancheru':")
result = sb.table('locations').select('*').ilike('name', '%peerancheru%').execute()

if result.data:
    for loc in result.data:
        print(f"   ✅ Found: ID={loc['id']}, Name='{loc['name']}'")
        location_id = loc['id']
        location_name = loc['name']
else:
    print("   ❌ NOT FOUND in locations table")
    location_id = None
    location_name = None

if not location_id:
    print("\n⚠️  Peerancheru not found in locations table. Exiting.")
    exit()

# Step 2: Check unified_data table for this location
print(f"\n2. Checking unified_data table for location_id={location_id}:")
result = sb.table('unified_data').select('*').eq('location_id', location_id).execute()

print(f"   Total properties: {len(result.data)}")
if result.data:
    print(f"   Sample properties:")
    for prop in result.data[:3]:
        print(f"      - {prop.get('property_name', 'N/A')} | BHK: {prop.get('bhk', 'N/A')} | Price: {prop.get('price_per_sqft', 'N/A')}")
else:
    print("   ❌ NO PROPERTIES found in unified_data")

# Step 3: Check if there's a spelling mismatch
print(f"\n3. Checking for spelling variations in unified_data:")
result = sb.table('unified_data').select('location_name').ilike('location_name', '%peerancheru%').execute()
if result.data:
    unique_spellings = set([r['location_name'] for r in result.data])
    print(f"   Found {len(result.data)} properties with these spellings:")
    for spelling in unique_spellings:
        count = len([r for r in result.data if r['location_name'] == spelling])
        print(f"      - '{spelling}' ({count} properties)")
else:
    print("   ❌ NO properties found with 'peerancheru' in location_name")

# Step 4: Check API endpoint behavior
print(f"\n4. Testing API endpoint logic:")
print(f"   Location name in locations table: '{location_name}'")
print(f"   Location ID: {location_id}")

# Check what the API would return
result = sb.table('unified_data').select('*').eq('location_id', location_id).execute()
print(f"   Properties matching location_id={location_id}: {len(result.data)}")

print("\n" + "="*70)
print("DIAGNOSIS:")
print("="*70)
