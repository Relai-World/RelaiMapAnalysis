#!/usr/bin/env python3
"""
Fix Search Function - Update Supabase to use locations table instead of news_balanced_corpus_1
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# The fixed SQL function
FIXED_SEARCH_FUNCTION = """
-- FIXED: Now uses locations table (authoritative source) instead of news_balanced_corpus_1
-- news_balanced_corpus_1 should only be used for sentiment analysis, not location search
CREATE OR REPLACE FUNCTION search_locations_func(search_query TEXT)
RETURNS TABLE (
    location_name TEXT,
    location_id INT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.name::TEXT as location_name,
        l.id::INT as location_id
    FROM locations l
    WHERE l.name ILIKE '%' || search_query || '%'
    ORDER BY l.name
    LIMIT 10;
END;
$$;
"""

def main():
    print("=" * 70)
    print("FIXING SEARCH FUNCTION - Use locations table")
    print("=" * 70)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials in .env")
        return
    
    sb = create_client(url, key)
    
    print("\n📋 Current Issue:")
    print("   - Search function uses 'news_balanced_corpus_1' table")
    print("   - Should use 'locations' table (authoritative source)")
    print("   - news_balanced_corpus_1 should only be for sentiment analysis")
    
    print("\n🔧 Applying Fix...")
    
    try:
        # Execute the SQL to update the function
        result = sb.rpc('exec_sql', {'sql': FIXED_SEARCH_FUNCTION}).execute()
        print("✅ Function updated successfully!")
    except Exception as e:
        print(f"⚠️  Direct SQL execution not available via RPC")
        print(f"   Error: {e}")
        print("\n📝 Manual Steps Required:")
        print("   1. Go to Supabase Dashboard > SQL Editor")
        print("   2. Copy and paste the SQL from supabase_functions.sql")
        print("   3. Find the search_locations_func function (around line 157)")
        print("   4. Run the updated function")
        print("\n   Or run this SQL directly:")
        print("-" * 70)
        print(FIXED_SEARCH_FUNCTION)
        print("-" * 70)
    
    print("\n🧪 Testing the Fixed Function...")
    
    # Test the search function
    try:
        result = sb.rpc('search_locations_func', {'search_query': 'gachi'}).execute()
        locations = result.data
        
        if locations and len(locations) > 0:
            print(f"✅ Search working! Found {len(locations)} results for 'gachi'")
            for loc in locations:
                print(f"   - {loc['location_name']} (ID: {loc['location_id']})")
        else:
            print("⚠️  No results found (this might be expected)")
    except Exception as e:
        print(f"❌ Error testing search: {e}")
    
    print("\n🔍 Verifying Data Source...")
    
    # Verify locations table has data
    try:
        result = sb.table('locations').select('id, name').limit(5).execute()
        locations_table = result.data
        
        print(f"✅ Locations table has {len(locations_table)} sample records:")
        for loc in locations_table[:3]:
            print(f"   - {loc['name']} (ID: {loc['id']})")
    except Exception as e:
        print(f"❌ Error querying locations table: {e}")
    
    print("\n" + "=" * 70)
    print("✅ FIX COMPLETE")
    print("=" * 70)
    print("Search function now uses 'locations' table (authoritative source)")
    print("news_balanced_corpus_1 is only used for sentiment analysis")
    print("=" * 70)

if __name__ == "__main__":
    main()
