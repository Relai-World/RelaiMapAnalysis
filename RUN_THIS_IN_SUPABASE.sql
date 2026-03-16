-- =====================================================
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================
-- This will update the search function to use locations table
-- instead of news_balanced_corpus_1
-- =====================================================

-- Step 1: Drop the old function (clean slate)
DROP FUNCTION IF EXISTS search_locations_func(TEXT);

-- Step 2: Create the corrected function
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

-- Step 3: Grant permissions to anon role (for frontend access)
GRANT EXECUTE ON FUNCTION search_locations_func(TEXT) TO anon;

-- Step 4: Test the function
SELECT 'Testing search function...' as status;
SELECT * FROM search_locations_func('appa');

-- Expected result: Only ONE "Appa Junction" from locations table
-- If you see TWO results, the function is still using the old code
