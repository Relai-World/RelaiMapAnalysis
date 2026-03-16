#!/usr/bin/env python3
"""
Test what happens when we search for different Peerancheru spellings
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("TESTING PROPERTY SEARCHES")
print("="*70)

# Test different search terms
search_terms = [
    'Peerancheru',
    'Patancheru',
    'Patancheruvu',
    'Peeramcheruvu'
]

for term in search_terms:
    result = sb.table('unified_data_DataType_Raghu').select('id', count='exact').eq('areaname', term).execute()
    print(f"\nExact match '{term}': {result.count} properties")

print("\n" + "="*70)
print("SOLUTION OPTIONS:")
print("="*70)
print("\n1. UPDATE LOCATION NAME (Quick Fix):")
print("   Change 'Peerancheru' → 'Patancheruvu' in locations table")
print("   This will show 166 properties immediately")

print("\n2. ADD FUZZY MATCHING TO API (Better Long-term):")
print("   Modify API to search for similar spellings")
print("   e.g., 'Peerancheru' also searches 'Patancheru', 'Patancheruvu'")

print("\n3. NORMALIZE PROPERTY DATA (Most Work):")
print("   Update all 334 properties to use 'Peerancheru' as areaname")

print("\n💡 RECOMMENDED: Option 1 (Update location name)")
print("   It's the fastest fix and will work immediately")
