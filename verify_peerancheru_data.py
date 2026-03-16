#!/usr/bin/env python3
"""
Verify the exact property data for Peerancheru
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("VERIFYING PEERANCHERU PROPERTY DATA")
print("="*70)

# Get ALL properties that contain "peer" in areaname
result = sb.table('unified_data_DataType_Raghu').select('*').ilike('areaname', '%peer%').execute()

print(f"\nTotal properties with 'peer' in areaname: {len(result.data)}")

# Group by exact areaname
from collections import defaultdict
by_area = defaultdict(list)
for prop in result.data:
    area = prop.get('areaname', 'NULL')
    by_area[area].append(prop)

print("\nBreakdown by areaname:")
for area, props in sorted(by_area.items()):
    print(f"\n   '{area}': {len(props)} properties")
    # Show first property details
    if props:
        p = props[0]
        print(f"      Project: {p.get('projectname')}")
        print(f"      City: {p.get('city')}")
        print(f"      Status: {p.get('isavailable')}")
        print(f"      BHK: {p.get('bhk')}")

# Now test the exact SQL query the API would use
print("\n" + "="*70)
print("TESTING API SQL QUERY:")
print("="*70)

search_term = "Peerancheru"
print(f"\nSearch term: '{search_term}'")

# Test each condition
conditions = [
    ("Exact match", f"areaname = '{search_term}'"),
    ("Ends with space", f"areaname LIKE '% {search_term}'"),
    ("Starts with comma", f"areaname LIKE '{search_term}, %'"),
]

for name, condition in conditions:
    # Use raw SQL-like filtering
    if "LIKE '%" in condition:
        pattern = condition.split("LIKE ")[1].strip("'")
        result = sb.table('unified_data_DataType_Raghu').select('areaname, projectname', count='exact').ilike('areaname', pattern).execute()
    else:
        result = sb.table('unified_data_DataType_Raghu').select('areaname, projectname', count='exact').eq('areaname', search_term).execute()
    
    print(f"\n{name}: {result.count} properties")
    if result.data:
        for p in result.data[:2]:
            print(f"   - {p['areaname']}: {p['projectname']}")
