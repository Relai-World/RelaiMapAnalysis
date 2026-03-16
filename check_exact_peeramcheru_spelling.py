#!/usr/bin/env python3
"""
Check the EXACT spelling of peeramcheru in unified_data_DataType_Raghu
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("CHECKING EXACT SPELLING IN unified_data_DataType_Raghu")
print("="*70)

# Search for all variations
variations = [
    'Peeramcheru',
    'Peeramcheruvu',
    'Peerancheru',
    'Peerancheruvu'
]

print("\nSearching for exact matches:")
for spelling in variations:
    result = sb.table('unified_data_DataType_Raghu').select('areaname, projectname', count='exact').eq('areaname', spelling).execute()
    if result.count > 0:
        print(f"\n✅ '{spelling}': {result.count} properties")
        for p in result.data[:3]:
            print(f"   - {p['projectname']}")
    else:
        print(f"❌ '{spelling}': 0 properties")

# Also search with LIKE to find any similar
print("\n" + "="*70)
print("Searching with LIKE '%peeramcher%':")
result = sb.table('unified_data_DataType_Raghu').select('areaname', count='exact').ilike('areaname', '%peeramcher%').execute()
print(f"Total matches: {result.count}")

if result.data:
    unique_names = set([r['areaname'] for r in result.data])
    print("\nUnique areaname values:")
    for name in sorted(unique_names):
        count = len([r for r in result.data if r['areaname'] == name])
        print(f"   '{name}': {count} properties")
