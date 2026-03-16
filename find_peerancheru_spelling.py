#!/usr/bin/env python3
"""
Find the correct spelling of Peerancheru in the database
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Searching for Peerancheru spelling variations:\n")

# Try different spellings
spellings = [
    'peerancheru',
    'peeran cheruvu',
    'peerancheruvu',
    'patancheru',
    'patancheruvu'
]

print("1. Checking locations table:")
for spelling in spellings:
    result = sb.table('locations').select('id, name').ilike('name', f'%{spelling}%').execute()
    if result.data:
        print(f"   ✅ '{spelling}' found:")
        for loc in result.data:
            print(f"      ID={loc['id']}, Name='{loc['name']}'")

print("\n2. Checking unified_data table for location_name:")
for spelling in spellings:
    result = sb.table('unified_data').select('location_name').ilike('location_name', f'%{spelling}%').limit(1).execute()
    if result.data:
        print(f"   ✅ '{spelling}' found in unified_data:")
        for loc in result.data:
            print(f"      location_name='{loc['location_name']}'")
