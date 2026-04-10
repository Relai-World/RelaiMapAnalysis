-- =====================================================
-- Nearby Properties Search Function
-- Finds properties within 1km radius of given coordinates
-- Handles both JSON and comma-separated coordinate formats
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS search_nearby_properties_func(NUMERIC, NUMERIC, NUMERIC);

-- Helper function to extract latitude from google_place_location
CREATE OR REPLACE FUNCTION extract_lat(location_text TEXT)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Try JSON format first
    IF location_text LIKE '{%' THEN
        RETURN (location_text::jsonb->>'lat')::NUMERIC;
    -- Try comma-separated format
    ELSIF location_text LIKE '%,%' THEN
        RETURN split_part(location_text, ',', 1)::NUMERIC;
    ELSE
        RETURN NULL;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$;

-- Helper function to extract longitude from google_place_location
CREATE OR REPLACE FUNCTION extract_lng(location_text TEXT)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    -- Try JSON format first
    IF location_text LIKE '{%' THEN
        RETURN (location_text::jsonb->>'lng')::NUMERIC;
    -- Try comma-separated format
    ELSIF location_text LIKE '%,%' THEN
        RETURN split_part(location_text, ',', 2)::NUMERIC;
    ELSE
        RETURN NULL;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$;

-- Create the nearby properties search function
CREATE OR REPLACE FUNCTION search_nearby_properties_func(
    search_lat NUMERIC,
    search_lng NUMERIC,
    radius_km NUMERIC DEFAULT 1.0
)
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
    google_place_location TEXT,
    distance_km NUMERIC
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
        u.google_place_location::TEXT,
        -- Calculate distance using Haversine formula
        (
            6371 * acos(
                LEAST(1.0, GREATEST(-1.0,
                    cos(radians(search_lat)) * 
                    cos(radians(extract_lat(u.google_place_location))) * 
                    cos(radians(extract_lng(u.google_place_location)) - radians(search_lng)) + 
                    sin(radians(search_lat)) * 
                    sin(radians(extract_lat(u.google_place_location)))
                ))
            )
        )::NUMERIC as distance_km
    FROM "unified_data_DataType_Raghu" u
    WHERE 
        u.google_place_location IS NOT NULL
        AND u.google_place_location != ''
        AND extract_lat(u.google_place_location) IS NOT NULL
        AND extract_lng(u.google_place_location) IS NOT NULL
        -- Filter by approximate bounding box first (faster)
        AND extract_lat(u.google_place_location) 
            BETWEEN (search_lat - (radius_km / 111.0)) AND (search_lat + (radius_km / 111.0))
        AND extract_lng(u.google_place_location) 
            BETWEEN (search_lng - (radius_km / 111.0)) AND (search_lng + (radius_km / 111.0))
    ORDER BY distance_km
    LIMIT 10;
END;
$$;

-- Grant permissions to anon role (for frontend access)
GRANT EXECUTE ON FUNCTION extract_lat(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION extract_lng(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION search_nearby_properties_func(NUMERIC, NUMERIC, NUMERIC) TO anon;

-- Test the function (example coordinates for Gachibowli, Hyderabad)
SELECT 'Testing nearby properties search function...' as status;
SELECT projectname, areaname, ROUND(distance_km::NUMERIC, 2) as distance_km 
FROM search_nearby_properties_func(17.4400, 78.3489, 1.0);

-- Expected result: Properties within 1km of the given coordinates
