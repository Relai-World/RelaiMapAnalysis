-- =====================================================
-- Global Property Search Function
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS search_properties_func(TEXT);

-- Create the property search function
CREATE OR REPLACE FUNCTION search_properties_func(search_query TEXT)
RETURNS TABLE (
    id INT,
    projectname TEXT,
    buildername TEXT,
    areaname TEXT,
    bhk TEXT,
    price_per_sft NUMERIC,
    sqfeet TEXT,
    city TEXT,
    project_type TEXT,
    construction_status TEXT,
    google_place_location TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id::INT,
        u.projectname::TEXT,
        u.buildername::TEXT,
        u.areaname::TEXT,
        u.bhk::TEXT,
        safe_numeric(u.price_per_sft)::NUMERIC,
        u.sqfeet::TEXT,
        u.city::TEXT,
        u.project_type::TEXT,
        u.construction_status::TEXT,
        u.google_place_location::TEXT
    FROM "unified_data_DataType_Raghu" u
    WHERE 
        u.projectname ILIKE '%' || search_query || '%'
        OR u.buildername ILIKE '%' || search_query || '%'
        OR u.areaname ILIKE '%' || search_query || '%'
        OR u.bhk::TEXT ILIKE '%' || search_query || '%'
    ORDER BY u.projectname, u.buildername
    LIMIT 20;
END;
$$;

-- Grant permissions to anon role (for frontend access)
GRANT EXECUTE ON FUNCTION search_properties_func(TEXT) TO anon;

-- Test the function
SELECT 'Testing property search function...' as status;
SELECT * FROM search_properties_func('prestige');

-- Expected result: Properties with "prestige" in name, builder, area, or BHK from both Hyderabad and Bangalore
