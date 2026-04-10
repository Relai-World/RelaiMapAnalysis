-- Test if the functions exist and work
-- Run this in Supabase SQL Editor to debug

-- Test 1: Check if functions exist
SELECT 'Checking if functions exist...' as status;

SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN ('search_nearby_locations_func', 'search_nearby_properties_func', 'extract_lat', 'extract_lng')
ORDER BY routine_name;

-- Test 2: Get Kokapet coordinates from locations table
SELECT 'Getting Kokapet coordinates...' as status;

SELECT 
    id,
    name,
    geom,
    -- Extract latitude from POINT(lng lat) format
    CASE
        WHEN geom LIKE 'POINT(%' THEN
            CAST(SPLIT_PART(REPLACE(REPLACE(geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
        ELSE NULL
    END as latitude,
    -- Extract longitude from POINT(lng lat) format
    CASE
        WHEN geom LIKE 'POINT(%' THEN
            CAST(SPLIT_PART(REPLACE(REPLACE(geom, 'POINT(', ''), ')', ''), ' ', 1) AS NUMERIC)
        ELSE NULL
    END as longitude
FROM locations
WHERE name ILIKE '%kokapet%'
LIMIT 5;

-- Test 3: Try to call the nearby locations function with Kokapet coordinates
-- Using approximate Kokapet coordinates: 17.4400, 78.3489
SELECT 'Testing nearby locations function with Kokapet coordinates...' as status;

SELECT 
    location_name, 
    latitude,
    longitude,
    ROUND(distance_km::NUMERIC, 2) as distance_km
FROM search_nearby_locations_func(17.4400, 78.3489, 1.0)
LIMIT 10;

-- Test 4: Try with 2km radius
SELECT 'Testing with 2km radius...' as status;

SELECT 
    location_name, 
    ROUND(distance_km::NUMERIC, 2) as distance_km
FROM search_nearby_locations_func(17.4400, 78.3489, 2.0)
LIMIT 10;

-- Test 5: Try with 5km radius
SELECT 'Testing with 5km radius...' as status;

SELECT 
    location_name, 
    ROUND(distance_km::NUMERIC, 2) as distance_km
FROM search_nearby_locations_func(17.4400, 78.3489, 5.0)
LIMIT 10;

-- Test 6: Check all locations within 10km to see what's nearby
SELECT 'All locations within 10km of Kokapet...' as status;

WITH location_distances AS (
    SELECT 
        l.name,
        l.geom,
        -- Extract coordinates
        CASE
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS NUMERIC)
            ELSE NULL
        END as lat,
        CASE
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 1) AS NUMERIC)
            ELSE NULL
        END as lng
    FROM locations l
    WHERE l.geom IS NOT NULL
        AND l.geom LIKE 'POINT(%'
)
SELECT 
    name,
    lat,
    lng,
    ROUND((
        6371 * acos(
            LEAST(1.0, GREATEST(-1.0,
                cos(radians(17.4400)) *
                cos(radians(lat)) *
                cos(radians(lng) - radians(78.3489)) +
                sin(radians(17.4400)) *
                sin(radians(lat))
            ))
        )
    )::NUMERIC, 2) as distance_km
FROM location_distances
WHERE lat IS NOT NULL AND lng IS NOT NULL
    AND (
        6371 * acos(
            LEAST(1.0, GREATEST(-1.0,
                cos(radians(17.4400)) *
                cos(radians(lat)) *
                cos(radians(lng) - radians(78.3489)) +
                sin(radians(17.4400)) *
                sin(radians(lat))
            ))
        )
    ) <= 10.0
ORDER BY distance_km
LIMIT 20;
