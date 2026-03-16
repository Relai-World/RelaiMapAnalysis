#!/usr/bin/env python3
"""
List all tables in Supabase to find the correct property table name
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb = create_client(url, key)

print("Checking available tables:\n")

# Try common table names
table_names = [
    'unified_data',
    'unified_data_DataType_Raghuthis',
    'properties',
    'property_data',
    'locations',
    'location_costs'
]

for table_name in table_names:
    try:
        result = sb.table(table_name).select('*').limit(1).execute()
        print(f"✅ {table_name} - EXISTS ({len(result.data)} sample records)")
        if result.data:
            print(f"   Columns: {', '.join(list(result.data[0].keys())[:10])}...")
    except Exception as e:
        print(f"❌ {table_name} - NOT FOUND")
