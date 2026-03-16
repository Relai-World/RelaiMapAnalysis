#!/usr/bin/env python3
"""
Generate comprehensive spelling fixes for all mismatches
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Generating comprehensive spelling fixes...\n")

# Get all locations
result = sb.rpc('get_all_insights').execute()
locations = result.data

# Get all unique areanames
result = sb.table('unified_data_DataType_Raghu').select('areaname').execute()
property_areas_list = [r['areaname'] for r in result.data if r['areaname']]

# Count properties per area
from collections import Counter
area_counts = Counter(property_areas_list)

fixes = []

for loc in locations:
    location_name = loc['location']
    reported_count = loc.get('property_count', 0)
    
    # Check exact match
    actual_count = area_counts.get(location_name, 0)
    
    if reported_count != actual_count and actual_count == 0:
        # Location has 0 exact matches, look for close matches
        
        # Check case-insensitive match
        for area, count in area_counts.items():
            if area.lower() == location_name.lower() and area != location_name:
                fixes.append({
                    'old': location_name,
                    'new': area,
                    'count': count,
                    'reason': 'case_mismatch'
                })
                break
        else:
            # Check with spaces removed
            loc_no_space = location_name.replace(' ', '').lower()
            for area, count in area_counts.items():
                if area.replace(' ', '').lower() == loc_no_space and area != location_name:
                    fixes.append({
                        'old': location_name,
                        'new': area,
                        'count': count,
                        'reason': 'space_mismatch'
                    })
                    break

print(f"Found {len(fixes)} automatic fixes\n")
print("="*70)
print("SQL FIXES:")
print("="*70)
print()

for fix in fixes:
    print(f"-- {fix['old']} → {fix['new']} ({fix['count']} properties, {fix['reason']})")
    # Escape single quotes in names
    old_escaped = fix['old'].replace("'", "''")
    new_escaped = fix['new'].replace("'", "''")
    print(f"UPDATE locations SET name = '{new_escaped}' WHERE name = '{old_escaped}';")
    print()

print(f"\nTotal fixes: {len(fixes)}")
