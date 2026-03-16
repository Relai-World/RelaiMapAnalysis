#!/usr/bin/env python3
"""
Update Supabase Function - Apply the fix to the actual database
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

def main():
    print("=" * 70)
    print("UPDATING SUPABASE SEARCH FUNCTION")
    print("=" * 70)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return
    
    print("\n⚠️  IMPORTANT: The SQL file has been updated, but the function")
    print("   in your Supabase DATABASE has NOT been updated yet.")
    print("\n📋 Current Status:")
    print("   - Local file (supabase_functions.sql): ✅ FIXED")
    print("   - Supabase database function: ❌ STILL OLD")
    
    print("\n" + "=" * 70)
    print("MANUAL UPDATE REQUIRED")
    print("=" * 70)
    
    print("\n🔧 Steps to fix:")
    print("\n1. Open Supabase Dashboard:")
    print(f"   {url.replace('https://', 'https://app.supabase.com/project/')}")
    
    print("\n2. Go to: SQL Editor (left sidebar)")
    
    print("\n3. Copy and paste this SQL:")
    print("-" * 70)
    
    sql = """-- Drop old function
DROP FUNCTION IF EXISTS search_locations_func(TEXT);

-- Create fixed function
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

-- Grant permissions
GRANT EXECUTE ON FUNCTION search_locations_func(TEXT) TO anon;

-- Test it
SELECT * FROM search_locations_func('appa');"""
    
    print(sql)
    print("-" * 70)
    
    print("\n4. Click 'Run' button")
    
    print("\n5. Verify the results show only locations from 'locations' table")
    
    print("\n" + "=" * 70)
    print("ALTERNATIVE: Use Supabase CLI")
    print("=" * 70)
    
    print("\nIf you have Supabase CLI installed:")
    print("  supabase db push")
    print("\nOr apply the migration:")
    print("  psql <your-connection-string> < apply_search_fix.sql")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
