#!/usr/bin/env python3
"""
Audit property counts across all tables to verify data integrity
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("PROPERTY COUNT AUDIT")
print("="*70)

# Get all locations with their property counts from get_all_insights
print("\n1. Getting location data from get_all_insights RPC...")
result = sb.rpc('get_all_insights').execute()
locations = result.data

print(f"   Total locations: {len(locations)}")

# Check a few sample locations
print("\n2. Checking property counts for sample locations:")
print("   (Comparing locations table vs actual properties in unified_data)")

sample_locations = locations  # ALL locations

mismatches = []

for loc in sample_locations:
    location_name = loc['location']
    reported_count = loc.get('property_count', 0)
    
    # Count actual properties in unified_data_DataType_Raghu
    result = sb.table('unified_data_DataType_Raghu').select('id', count='exact').eq('areaname', location_name).execute()
    actual_count = result.count
    
    match_status = "✅" if reported_count == actual_count else "❌"
    print(f"\n   {match_status} {location_name}")
    print(f"      Reported: {reported_count} | Actual: {actual_count}")
    
    if reported_count != actual_count:
        mismatches.append({
            'location': location_name,
            'reported': reported_count,
            'actual': actual_count,
            'difference': actual_count - reported_count
        })

print("\n" + "="*70)

if mismatches:
    print("MISMATCHES FOUND:")
    print("="*70)
    for m in mismatches:
        print(f"\n   Location: {m['location']}")
        print(f"   Reported: {m['reported']} | Actual: {m['actual']} | Diff: {m['difference']}")
    
    print(f"\n   Total mismatches: {len(mismatches)} out of {len(sample_locations)} checked")
else:
    print("✅ ALL COUNTS MATCH!")

# Check Peeramcheruvu specifically
print("\n" + "="*70)
print("3. Checking Peeramcheruvu specifically:")
print("="*70)

peeramcheruvu = [loc for loc in locations if loc['location'] == 'Peeramcheruvu']
if peeramcheruvu:
    loc = peeramcheruvu[0]
    print(f"\n   Location: {loc['location']}")
    print(f"   Reported property_count: {loc.get('property_count', 0)}")
    
    # Check actual count
    result = sb.table('unified_data_DataType_Raghu').select('id', count='exact').eq('areaname', 'Peeramcheruvu').execute()
    print(f"   Actual properties in unified_data: {result.count}")
    
    if loc.get('property_count', 0) == result.count:
        print(f"   ✅ Counts match!")
    else:
        print(f"   ❌ MISMATCH! Difference: {result.count - loc.get('property_count', 0)}")
else:
    print("   ❌ Peeramcheruvu not found in locations table")

print("\n" + "="*70)
print("RECOMMENDATION:")
print("="*70)
print("If mismatches are found, the property_count in locations table")
print("needs to be recalculated. This might be done by:")
print("1. A scheduled job that updates counts")
print("2. Running compute_location_insights.py")
print("3. Updating the get_all_insights RPC function")
