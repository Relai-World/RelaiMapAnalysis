#!/usr/bin/env python3
"""
Debug Appa Junction Search Issue
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def main():
    print("=" * 70)
    print("DEBUGGING APPA JUNCTION SEARCH")
    print("=" * 70)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    sb = create_client(url, key)
    
    print("\n1️⃣  SEARCH FUNCTION RESULTS (what user sees)")
    print("-" * 70)
    
    try:
        result = sb.rpc('search_locations_func', {'search_query': 'appa'}).execute()
        search_results = result.data
        
        print(f"Found {len(search_results)} results:")
        for item in search_results:
            print(f"  - {item['location_name']} (ID: {item['location_id']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n2️⃣  LOCATIONS TABLE (authoritative source)")
    print("-" * 70)
    
    try:
        result = sb.table('locations').select('id, name').ilike('name', '%appa%').execute()
        locations = result.data
        
        print(f"Found {len(locations)} locations:")
        for loc in locations:
            print(f"  - {loc['name']} (ID: {loc['id']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n3️⃣  NEWS_BALANCED_CORPUS_1 TABLE (should NOT be used for search)")
    print("-" * 70)
    
    try:
        result = sb.table('news_balanced_corpus_1').select('location_name, location_id').ilike('location_name', '%appa%').execute()
        news_locations = result.data
        
        # Get unique location names
        unique_names = {}
        for item in news_locations:
            name = item['location_name']
            if name not in unique_names:
                unique_names[name] = item['location_id']
        
        print(f"Found {len(unique_names)} unique location names:")
        for name, loc_id in unique_names.items():
            print(f"  - {name} (location_id: {loc_id})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n4️⃣  CHECKING SEARCH FUNCTION SOURCE CODE")
    print("-" * 70)
    
    # Try to get the function definition
    try:
        # This won't work via Supabase client, but we can check the file
        with open('supabase_functions.sql', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find the search function
        start = content.find('CREATE OR REPLACE FUNCTION search_locations_func')
        if start != -1:
            end = content.find('$$;', start) + 3
            func_def = content[start:end]
            
            if 'FROM locations l' in func_def:
                print("✅ Function uses: FROM locations l")
            elif 'FROM news_balanced_corpus_1' in func_def:
                print("❌ Function STILL uses: FROM news_balanced_corpus_1")
            else:
                print("⚠️  Cannot determine source table")
                
            print("\nFunction excerpt:")
            lines = func_def.split('\n')
            for line in lines[10:20]:  # Show middle part
                if 'FROM' in line or 'WHERE' in line:
                    print(f"  {line}")
    except Exception as e:
        print(f"⚠️  Could not read function: {e}")
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)

if __name__ == "__main__":
    main()
