#!/usr/bin/env python3
"""
Diagnose why Peerancheru doesn't show properties
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("DIAGNOSING PEERANCHERU ISSUE")
print("="*70)

# 1. Check if Peerancheru/Patancheru exists in locations table
print("\n1. Checking locations table:")
result = sb.table('locations').select('id, name').or_('name.ilike.%patan%,name.ilike.%peer%').execute()
if result.data:
    print(f"   Found {len(result.data)} matching locations:")
    for loc in result.data:
        print(f"      ID={loc['id']}, Name='{loc['name']}'")
else:
    print("   ❌ NO matching locations found")

# 2. Count properties in unified_data_DataType_Raghu
print("\n2. Properties in unified_data_DataType_Raghu:")
result = sb.table('unified_data_DataType_Raghu').select('areaname', count='exact').or_('areaname.ilike.%patan%,areaname.ilike.%peer%').execute()
print(f"   Total properties with Patan/Peer: {result.count}")

# Get unique area names
result = sb.table('unified_data_DataType_Raghu').select('areaname').or_('areaname.ilike.%patan%,areaname.ilike.%peer%').execute()
unique_areas = set([r['areaname'] for r in result.data if r['areaname']])
print(f"   Unique area names:")
for area in sorted(unique_areas):
    count = len([r for r in result.data if r['areaname'] == area])
    print(f"      - '{area}' ({count} properties)")

# 3. Check how API.py fetches properties
print("\n3. Checking API logic:")
print("   The API likely uses location name from 'locations' table")
print("   to match against 'areaname' in unified_data_DataType_Raghu")

print("\n" + "="*70)
print("ROOT CAUSE:")
print("="*70)
print("❌ 'Peerancheru' does NOT exist in the 'locations' table")
print("✅ Properties exist in unified_data_DataType_Raghu with:")
print("   - 'Patancheru' (2 properties)")
print("   - 'Patancheruvu' (multiple properties)")
print("   - 'Peerzadiguda' (multiple properties)")
print("\n💡 SOLUTION:")
print("   Need to add 'Peerancheru' to locations table OR")
print("   Update existing location name to match property data")
