#!/usr/bin/env python3
"""
Check if future_development_scrap table exists and is ready
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Checking future_development_scrap table:\n")

try:
    # Try to query the table
    result = sb.table('future_development_scrap').select('*').limit(5).execute()
    
    print(f"✅ Table exists!")
    print(f"   Current records: {len(result.data)}")
    
    if result.data:
        print(f"\n   Sample records:")
        for record in result.data[:3]:
            print(f"   - Location: {record.get('location_name')}")
            print(f"     Year: {record.get('year_mentioned')}")
            print(f"     URL: {record.get('url')[:60]}...")
            print()
    else:
        print(f"\n   Table is empty - ready for scraping!")
    
except Exception as e:
    print(f"❌ Table check failed: {e}")
    print(f"\n⚠️  You need to run create_future_development_table.sql in Supabase SQL Editor")
    print(f"   File location: create_future_development_table.sql")
