#!/usr/bin/env python3
"""
Debug why locations fetch returns empty
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Testing different ways to fetch locations:\n")

# Method 1: Direct table query
print("1. Direct table query:")
try:
    result = sb.table('locations').select('id, name').limit(5).execute()
    print(f"   Result: {len(result.data) if result.data else 0} rows")
    if result.data:
        print(f"   Sample: {result.data[0]}")
except Exception as e:
    print(f"   Error: {e}")

# Method 2: Using RPC (get_all_insights)
print("\n2. Using RPC get_all_insights:")
try:
    result = sb.rpc('get_all_insights').execute()
    print(f"   Result: {len(result.data) if result.data else 0} rows")
    if result.data:
        print(f"   Sample: {result.data[0]['location']} (ID: {result.data[0]['location_id']})")
except Exception as e:
    print(f"   Error: {e}")

# Method 3: Check table permissions
print("\n3. Checking table structure:")
try:
    result = sb.table('locations').select('*').limit(1).execute()
    if result.data:
        print(f"   Columns: {list(result.data[0].keys())}")
    else:
        print("   No data returned")
except Exception as e:
    print(f"   Error: {e}")
