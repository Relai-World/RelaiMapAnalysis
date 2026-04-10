-- =====================================================
-- FIX: Update get_property_costs_func to handle plural/singular variations
-- This fixes the issue where "Dollar Hills" doesn't match "Dollar hill"
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================

CREATE OR REPLACE FUNCTION get_property_costs_func(area_name TEXT)
RETURNS TABLE (
    location TEXT,
    count INT,
    avgBase FLOAT,
    avgSqft FLOAT,
    minBase FLOAT,
    maxBase FLOAT,
    minSqft FLOAT,
    maxSqft FLOAT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        area_name::TEXT,
        COUNT(*)::INT,
        ROUND((AVG(safe_numeric(baseprojectprice)) / 10000000)::NUMERIC, 2)::FLOAT,
        ROUND(AVG(safe_numeric(price_per_sft))::NUMERIC, 0)::FLOAT,
        ROUND((MIN(safe_numeric(baseprojectprice)) / 10000000)::NUMERIC, 2)::FLOAT,
        ROUND((MAX(safe_numeric(baseprojectprice)) / 10000000)::NUMERIC, 2)::FLOAT,
        ROUND(MIN(safe_numeric(price_per_sft))::NUMERIC, 0)::FLOAT,
        ROUND(MAX(safe_numeric(price_per_sft))::NUMERIC, 0)::FLOAT
    FROM "unified_data_DataType_Raghu" 
    WHERE (
        -- Exact match (case insensitive)
        LOWER(areaname) = LOWER(area_name)
        -- Match without spaces
        OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(area_name, ' ', ''))
        -- Match with comma variations
        OR areaname ILIKE area_name
        OR area_name ILIKE areaname
        -- NEW: Fuzzy match - handles plural/singular (Dollar Hills vs Dollar hill)
        OR LOWER(areaname) LIKE LOWER(area_name) || '%'
        OR LOWER(area_name) LIKE LOWER(areaname) || '%'
    )
    AND safe_numeric(price_per_sft) > 0
    AND safe_numeric(baseprojectprice) > 0;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION get_property_costs_func(TEXT) TO anon;

-- Test the fix
SELECT 'Testing Dollar Hills property costs...' as status;
SELECT location, count, avgSqft, minSqft, maxSqft
FROM get_property_costs_func('Dollar Hills');

SELECT '✅ Function updated! Now "Dollar Hills" will match "Dollar hill" for property costs' as status;
