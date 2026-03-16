#!/usr/bin/env python3
"""
Check unified_data table schema
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Checking unified_data table schema:\n")

# Get one record to see all columns
result = sb.table('unified_data').select('*').limit(1).execute()

if result.data:
    print("Columns in unified_data table:")
    for key in result.data[0].keys():
        print(f"   - {key}")
    
    print("\nSample record:")
    for key, value in result.data[0].items():
        print(f"   {key}: {value}")
else:
    print("No data in unified_data table")
