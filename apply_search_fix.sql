-- =====================================================
-- FIX: Update search_locations_func to use locations table
-- =====================================================
-- 
-- ISSUE: Search function was using news_balanced_corpus_1 table
-- FIX: Now uses locations table (authoritative source)
-- 
-- Run this in Supabase Dashboard > SQL Editor
-- =====================================================

-- Drop the old function first (optional, but ensures clean update)
DROP FUNCTION IF EXISTS search_locations_func(TEXT);

-- Create the fixed function that uses locations table
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

-- Grant execute permission to anon role (for frontend access)
GRANT EXECUTE ON FUNCTION search_locations_func(TEXT) TO anon;

-- Test the function
SELECT * FROM search_locations_func('gachi');

-- Verify it returns results from locations table
SELECT 'Fix applied successfully!' as status;
