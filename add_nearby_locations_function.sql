-- =====================================================
-- Nearby Locations Search Function
-- Finds locations within specified radius of given coordinates
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS search_nearby_locations_func(NUMERIC, NUMERIC, NUMERIC);

-- Create the nearby locations search function
CREATE OR REPLACE FUNCTION search_nearby_locations_func(
    search_lat NUMERIC,
    search_lng NUMERIC,
    radius_km NUMERIC DEFAULT 1.0
)
RETURNS TABLE (
    location_id INT,
    location_name TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    distance_km NUMERIC
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id::INT as location_id,
        l.name::TEXT as location_name,
        -- Extract latitude from POINT(lng lat) format
        CASE 
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
            ELSE NULL
        END as latitude,
        -- Extract longitude from POINT(lng lat) format
        CASE 
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 1) AS NUMERIC)
            ELSE NULL
        END as longitude,
        -- Calculate distance using Haversine formula
        (
            6371 * acos(
                LEAST(1.0, GREATEST(-1.0,
                    cos(radians(search_lat)) * 
                    cos(radians(
                        CASE 
                            WHEN l.geom LIKE 'POINT(%' THEN
                                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
                            ELSE NULL
                        END
                    )) * 
                    cos(radians(
                        CASE 
                            WHEN l.geom LIKE 'POINT(%' THEN
                                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 1) AS NUMERIC)
                            ELSE NULL
                        END
                    ) - radians(search_lng)) + 
                    sin(radians(search_lat)) * 
                    sin(radians(
                        CASE 
                            WHEN l.geom LIKE 'POINT(%' THEN
                                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
                            ELSE NULL
                        END
                    ))
                ))
            )
        )::NUMERIC as distance_km
    FROM locations l
    WHERE 
        l.geom IS NOT NULL
        AND l.geom LIKE 'POINT(%'
        -- Calculate actual distance and filter
        AND (
            6371 * acos(
                LEAST(1.0, GREATEST(-1.0,
                    cos(radians(search_lat)) * 
                    cos(radians(
                        CASE 
                            WHEN l.geom LIKE 'POINT(%' THEN
                                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
                            ELSE NULL
                        END
                    )) * 
                    cos(radians(
                        CASE 
                            WHEN l.geom LIKE 'POINT(%' THEN
                                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 1) AS NUMERIC)
                            ELSE NULL
                        END
                    ) - radians(search_lng)) + 
                    sin(radians(search_lat)) * 
                    sin(radians(
                        CASE 
                            WHEN l.geom LIKE 'POINT(%' THEN
                                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
                            ELSE NULL
                        END
                    ))
                ))
            )
        ) <= radius_km
    ORDER BY distance_km
    LIMIT 10;
END;
$$;

-- Grant permissions to anon role (for frontend access)
GRANT EXECUTE ON FUNCTION search_nearby_locations_func(NUMERIC, NUMERIC, NUMERIC) TO anon;

-- Test the function (example coordinates for Kokapet, Hyderabad)
SELECT 'Testing nearby locations search function...' as status;
SELECT location_name, ROUND(distance_km::NUMERIC, 2) as distance_km 
FROM search_nearby_locations_func(17.4400, 78.3489, 1.0);

-- Expected result: Locations within 1km of Kokapet
