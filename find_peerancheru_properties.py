#!/usr/bin/env python3
"""
Find Peerancheru in unified_data_DataType_Raghu and locations tables
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("="*70)
print("SEARCHING FOR PEERANCHERU")
print("="*70)

# Search in locations table with variations
print("\n1. Searching locations table:")
variations = ['peer', 'patan', 'peran']
for var in variations:
    result = sb.table('locations').select('id, name').ilike('name', f'%{var}%').execute()
    if result.data:
        print(f"\n   Matches for '{var}':")
        for loc in result.data:
            print(f"      ID={loc['id']}, Name='{loc['name']}'")

# Search in unified_data_DataType_Raghu by areaname
print("\n2. Searching unified_data_DataType_Raghu.areaname:")
for var in variations:
    result = sb.table('unified_data_DataType_Raghu').select('areaname, projectname, city').ilike('areaname', f'%{var}%').limit(5).execute()
    if result.data:
        print(f"\n   Matches for '{var}' in areaname:")
        for prop in result.data:
            print(f"      Area: {prop['areaname']}, Project: {prop['projectname']}, City: {prop['city']}")

# Search in unified_data_DataType_Raghu by projectlocation
print("\n3. Searching unified_data_DataType_Raghu.projectlocation:")
for var in variations:
    result = sb.table('unified_data_DataType_Raghu').select('projectlocation, projectname, city').ilike('projectlocation', f'%{var}%').limit(5).execute()
    if result.data:
        print(f"\n   Matches for '{var}' in projectlocation:")
        for prop in result.data:
            print(f"      Location: {prop['projectlocation']}, Project: {prop['projectname']}, City: {prop['city']}")
