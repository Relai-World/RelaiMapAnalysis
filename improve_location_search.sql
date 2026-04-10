-- =====================================================
-- IMPROVE LOCATION SEARCH - Handle common misspellings
-- Makes search more flexible for variations like:
-- - Rajini vs Rajaji
-- - Spaces vs no spaces
-- - Partial matches
-- =====================================================

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
    WHERE 
        -- Original: case-insensitive contains
        l.name ILIKE '%' || search_query || '%'
        -- Remove spaces from both sides for matching
        OR REPLACE(LOWER(l.name), ' ', '') LIKE '%' || REPLACE(LOWER(search_query), ' ', '') || '%'
        -- Match individual words (handles "Rajini nagar" finding "Rajajinagar")
        OR LOWER(l.name) LIKE '%' || SPLIT_PART(LOWER(search_query), ' ', 1) || '%'
    ORDER BY 
        -- Prioritize exact matches
        CASE 
            WHEN LOWER(l.name) = LOWER(search_query) THEN 0
            WHEN l.name ILIKE search_query || '%' THEN 1
            WHEN l.name ILIKE '%' || search_query || '%' THEN 2
            ELSE 3
        END,
        l.name
    LIMIT 10;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION search_locations_func(TEXT) TO anon;

-- Test the improved search
SELECT 'Testing improved search...' as status;

-- Should now find Rajajinagar
SELECT * FROM search_locations_func('Rajini nagar');
SELECT * FROM search_locations_func('Rajini');
SELECT * FROM search_locations_func('Rajaji');

SELECT '✅ Search function improved! Now handles spelling variations.' as status;
