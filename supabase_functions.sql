-- =====================================================
-- SUPABASE RPC FUNCTIONS FOR HYDERABAD REAL ESTATE INTELLIGENCE
-- Run these in Supabase SQL Editor to create functions
-- that can be called via REST API with anon key
-- =====================================================

-- Helper function to safely cast text to numeric (handles "None", empty strings, etc.)
CREATE OR REPLACE FUNCTION safe_numeric(val TEXT)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF val IS NULL OR val = '' OR val = 'None' OR NOT (val ~ '^[0-9]+\.?[0-9]*$') THEN
        RETURN NULL;
    END IF;
    RETURN CAST(val AS NUMERIC);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$;

-- Overload for INTEGER type
CREATE OR REPLACE FUNCTION safe_numeric(val INTEGER)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    RETURN val::NUMERIC;
END;
$$;

-- Overload for BIGINT type
CREATE OR REPLACE FUNCTION safe_numeric(val BIGINT)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    RETURN val::NUMERIC;
END;
$$;

-- =====================================================
-- Function 1: Get all insights (Main map data)
-- Endpoint: /api/v1/insights
-- =====================================================
CREATE OR REPLACE FUNCTION get_all_insights()
RETURNS TABLE (
    location_id INT,
    location TEXT,
    longitude FLOAT,
    latitude FLOAT,
    avg_sentiment FLOAT,
    growth_score FLOAT,
    investment_score FLOAT,
    article_count INT,
    avg_property_price FLOAT,
    property_count INT,
    min_property_price FLOAT,
    max_property_price FLOAT,
    price_summary TEXT,
    sentiment_summary TEXT,
    growth_summary TEXT,
    invest_summary TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    WITH property_stats AS (
        SELECT 
            LOWER(areaname) as area_lower,
            areaname as original_area,
            COUNT(*) as property_count,
            AVG(safe_numeric(price_per_sft)) as avg_price_per_sft,
            MIN(safe_numeric(price_per_sft)) as min_price_per_sft,
            MAX(safe_numeric(price_per_sft)) as max_price_per_sft
        FROM "unified_data_DataType_Raghu" 
        WHERE safe_numeric(price_per_sft) > 0
        GROUP BY LOWER(areaname), areaname
    ),
    location_property_matches AS (
        SELECT 
            l.id as loc_id,
            l.name as loc_name,
            SUM(ps.property_count) as total_property_count,
            AVG(ps.avg_price_per_sft) as avg_price_per_sft,
            MIN(ps.min_price_per_sft) as min_price_per_sft,
            MAX(ps.max_price_per_sft) as max_price_per_sft
        FROM locations l
        LEFT JOIN property_stats ps ON (
            -- Exact match with TRIM to handle trailing spaces
            LOWER(TRIM(ps.original_area)) = LOWER(TRIM(l.name))
            -- Match without spaces
            OR LOWER(REPLACE(TRIM(ps.original_area), ' ', '')) = LOWER(REPLACE(TRIM(l.name), ' ', ''))
            -- Pattern matching with TRIM
            OR TRIM(ps.original_area) ILIKE TRIM(l.name)
            OR TRIM(l.name) ILIKE TRIM(ps.original_area)
        )
        GROUP BY l.id, l.name
    ),
    article_stats AS (
        SELECT 
            nbc.location_id as art_loc_id,
            COUNT(*) as article_count
        FROM news_balanced_corpus_1 nbc
        GROUP BY nbc.location_id
    )
    SELECT
        l.id::INT,
        l.name::TEXT,
        -- Parse POINT(x y) format manually
        CASE 
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 1) AS FLOAT)
            ELSE NULL
        END,
        CASE 
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS FLOAT)
            ELSE NULL
        END,
        COALESCE(li.avg_sentiment_score, 0)::FLOAT,
        COALESCE(li.growth_score, 0)::FLOAT,
        COALESCE(li.investment_score, 0)::FLOAT,
        COALESCE(a.article_count, 0)::INT,
        COALESCE(lpm.avg_price_per_sft, 0)::FLOAT,
        COALESCE(lpm.total_property_count, 0)::INT,
        COALESCE(lpm.min_price_per_sft, 0)::FLOAT,
        COALESCE(lpm.max_price_per_sft, 0)::FLOAT,
        -- Generate price summary
        CASE 
            WHEN COALESCE(lpm.total_property_count, 0) > 0 THEN
                CASE 
                    WHEN COALESCE(lpm.min_price_per_sft, 0) = COALESCE(lpm.max_price_per_sft, 0) THEN
                        'Properties priced at ₹' || ROUND(COALESCE(lpm.avg_price_per_sft, 0))::TEXT || '/sqft (' || COALESCE(lpm.total_property_count, 0)::TEXT || ' properties available)'
                    ELSE
                        'Properties range from ₹' || ROUND(COALESCE(lpm.min_price_per_sft, 0))::TEXT || ' to ₹' || ROUND(COALESCE(lpm.max_price_per_sft, 0))::TEXT || '/sqft (avg ₹' || ROUND(COALESCE(lpm.avg_price_per_sft, 0))::TEXT || '/sqft, ' || COALESCE(lpm.total_property_count, 0)::TEXT || ' properties)'
                END
            ELSE 'No property pricing data available'
        END::TEXT,
        COALESCE(li.sentiment_summary, 'Sentiment is stable across major news outlets.')::TEXT,
        COALESCE(li.growth_summary, 'Infrastructure is developing steadily.')::TEXT,
        COALESCE(li.invest_summary, 'Prices show consistent long-term appreciation.')::TEXT
    FROM locations l
    LEFT JOIN location_insights li ON li.location_id = l.id
    LEFT JOIN location_property_matches lpm ON lpm.loc_id = l.id
    LEFT JOIN article_stats a ON a.art_loc_id = l.id
    ORDER BY l.name;
END;
$$;

-- =====================================================
-- Function 2: Search locations
-- Endpoint: /api/v1/search?q=<query>
-- =====================================================
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

-- =====================================================
-- Function 3: Get location price trends
-- Endpoint: /api/v1/location/{location_id}/trends
-- =====================================================
CREATE OR REPLACE FUNCTION get_location_trends_func(loc_id INT)
RETURNS TABLE (
    location_id INT,
    location TEXT,
    growth_yoy FLOAT,
    cagr FLOAT,
    trends JSONB
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    loc_name TEXT;
    trends_array JSONB;
    start_price FLOAT;
    current_price FLOAT;
    prev_price FLOAT;
    years_span INT;
    calc_growth_yoy FLOAT := 0.0;
    calc_cagr FLOAT := 0.0;
BEGIN
    -- Get location name
    SELECT name INTO loc_name FROM locations WHERE id = loc_id;
    
    IF loc_name IS NULL THEN
        RETURN;
    END IF;
    
    -- Build trends array from price_trends table
    SELECT jsonb_agg(
        jsonb_build_object('year', year_val, 'price', price_val)
        ORDER BY year_val
    ) INTO trends_array
    FROM (
        SELECT 2020 as year_val, year_2020 as price_val FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2020 IS NOT NULL
        UNION ALL
        SELECT 2021, year_2021 FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2021 IS NOT NULL
        UNION ALL
        SELECT 2022, year_2022 FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2022 IS NOT NULL
        UNION ALL
        SELECT 2023, year_2023 FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2023 IS NOT NULL
        UNION ALL
        SELECT 2024, year_2024 FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2024 IS NOT NULL
        UNION ALL
        SELECT 2025, year_2025 FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2025 IS NOT NULL
        UNION ALL
        SELECT 2026, year_2026 FROM price_trends WHERE LOWER(price_trends.location) = LOWER(loc_name) AND year_2026 IS NOT NULL
    ) t;
    
    -- Calculate growth metrics if we have data
    IF trends_array IS NOT NULL AND jsonb_array_length(trends_array) >= 2 THEN
        -- Get first and last prices
        start_price := (trends_array->0->>'price')::FLOAT;
        current_price := (trends_array->(jsonb_array_length(trends_array)-1)->>'price')::FLOAT;
        
        -- YoY growth (last year vs previous year)
        IF jsonb_array_length(trends_array) >= 2 THEN
            prev_price := (trends_array->(jsonb_array_length(trends_array)-2)->>'price')::FLOAT;
            IF prev_price > 0 THEN
                calc_growth_yoy := ROUND((((current_price - prev_price) / prev_price) * 100)::NUMERIC, 1);
            END IF;
        END IF;
        
        -- CAGR calculation
        years_span := (trends_array->(jsonb_array_length(trends_array)-1)->>'year')::INT - (trends_array->0->>'year')::INT;
        IF start_price > 0 AND years_span > 0 THEN
            calc_cagr := ROUND(((POWER(current_price / start_price, 1.0 / years_span) - 1) * 100)::NUMERIC, 1);
        END IF;
    END IF;
    
    RETURN QUERY SELECT 
        loc_id,
        loc_name,
        calc_growth_yoy,
        calc_cagr,
        COALESCE(trends_array, '[]'::JSONB);
END;
$$;

-- =====================================================
-- Function 4: Get property costs for specific location
-- Endpoint: /api/v1/property-costs/{area_name}
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
    WHERE (LOWER(areaname) = LOWER(area_name)
           OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(area_name, ' ', ''))
           OR areaname ILIKE area_name
           OR area_name ILIKE areaname)
        AND safe_numeric(price_per_sft) > 0
        AND safe_numeric(baseprojectprice) > 0;
END;
$$;

-- =====================================================
-- Function 5: Get properties by area with optional BHK filter
-- Endpoint: /api/v1/properties?area=<area>&bhk=<bhk>
-- =====================================================
CREATE OR REPLACE FUNCTION get_properties_func(area_name TEXT, bhk_filter TEXT DEFAULT NULL)
RETURNS TABLE (
    id INT,
    projectname TEXT,
    buildername TEXT,
    project_type TEXT,
    bhk TEXT,
    sqfeet TEXT,
    price_per_sft FLOAT,
    construction_status TEXT,
    areaname TEXT,
    images TEXT,
    google_place_location TEXT,
    full_details JSONB
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
        u.project_type::TEXT,
        u.bhk::TEXT,
        u.sqfeet::TEXT,
        safe_numeric(u.price_per_sft)::FLOAT,
        u.construction_status::TEXT,
        u.areaname::TEXT,
        u.images::TEXT,
        u.google_place_location::TEXT,
        -- Full details as JSONB (split into smaller objects to avoid 100-arg limit)
        jsonb_build_object(
            'projectname', u.projectname,
            'buildername', u.buildername,
            'project_type', u.project_type,
            'bhk', u.bhk,
            'sqfeet', u.sqfeet,
            'price_per_sft', safe_numeric(u.price_per_sft),
            'construction_status', u.construction_status,
            'areaname', u.areaname,
            'images', u.images
        ) || jsonb_build_object(
            'communitytype', u.communitytype,
            'status', u.status,
            'project_status', u.project_status,
            'isavailable', u.isavailable,
            'projectlocation', u.projectlocation,
            'google_place_name', u.google_place_name,
            'google_place_address', u.google_place_address,
            'google_maps_location', u.google_maps_location,
            'mobile_google_map_url', u.mobile_google_map_url
        ) || jsonb_build_object(
            'baseprojectprice', safe_numeric(u.baseprojectprice),
            'price_per_sft', safe_numeric(u.price_per_sft),
            'total_buildup_area', u.total_buildup_area,
            'price_per_sft_update_date', u.price_per_sft_update_date,
            'floor_rise_charges', u.floor_rise_charges,
            'floor_rise_amount_per_floor', u.floor_rise_amount_per_floor,
            'floor_rise_applicable_above_floor_no', u.floor_rise_applicable_above_floor_no,
            'facing_charges', u.facing_charges,
            'preferential_location_charges', u.preferential_location_charges,
            'preferential_location_charges_conditions', u.preferential_location_charges_conditions
        ) || jsonb_build_object(
            'amount_for_extra_car_parking', u.amount_for_extra_car_parking,
            'project_launch_date', u.project_launch_date,
            'possession_date', u.possession_date,
            'construction_status', u.construction_status,
            'construction_material', u.construction_material,
            'total_land_area', u.total_land_area,
            'number_of_towers', u.number_of_towers,
            'number_of_floors', u.number_of_floors,
            'number_of_flats_per_floor', u.number_of_flats_per_floor,
            'total_number_of_units', u.total_number_of_units
        ) || jsonb_build_object(
            'open_space', u.open_space,
            'carpet_area_percentage', u.carpet_area_percentage,
            'floor_to_ceiling_height', u.floor_to_ceiling_height,
            'bhk', u.bhk,
            'sqfeet', u.sqfeet,
            'sqyard', u.sqyard,
            'facing', u.facing,
            'no_of_car_parkings', u.no_of_car_parkings,
            'external_amenities', u.external_amenities,
            'specification', u.specification
        ) || jsonb_build_object(
            'powerbackup', u.powerbackup,
            'no_of_passenger_lift', u.no_of_passenger_lift,
            'no_of_service_lift', u.no_of_service_lift,
            'visitor_parking', u.visitor_parking,
            'ground_vehicle_movement', u.ground_vehicle_movement,
            'main_door_height', u.main_door_height,
            'home_loan', u.home_loan,
            'available_banks_for_loan', u.available_banks_for_loan,
            'builder_age', u.builder_age,
            'builder_completed_properties', u.builder_completed_properties
        ) || jsonb_build_object(
            'builder_ongoing_projects', u.builder_ongoing_projects,
            'builder_upcoming_properties', u.builder_upcoming_properties,
            'builder_total_properties', u.builder_total_properties,
            'builder_operating_locations', u.builder_operating_locations,
            'builder_origin_city', u.builder_origin_city,
            'poc_name', u.poc_name,
            'poc_contact', u.poc_contact,
            'poc_role', u.poc_role,
            'alternative_contact', u.alternative_contact,
            'useremail', u.useremail
        ) || jsonb_build_object(
            'google_place_rating', safe_numeric(u.google_place_rating),
            'google_place_user_ratings_total', u.google_place_user_ratings_total,
            'rera_number', u.rera_number
        )
    FROM "unified_data_DataType_Raghu" u
    WHERE (
        LOWER(u.areaname) = LOWER(area_name)
        OR LOWER(REPLACE(u.areaname, ' ', '')) = LOWER(REPLACE(area_name, ' ', ''))
        OR LOWER(u.areaname) LIKE LOWER(area_name) || ', %'
        OR LOWER(u.areaname) LIKE '%' || LOWER(area_name) || ', %'
        OR LOWER(u.areaname) LIKE '%,' || LOWER(area_name)
    )
    AND (bhk_filter IS NULL OR u.bhk::TEXT = bhk_filter OR u.bhk::TEXT = bhk_filter || '.0')
    ORDER BY
        CASE
            WHEN LOWER(u.areaname) = LOWER(area_name) THEN 0
            WHEN LOWER(REPLACE(u.areaname, ' ', '')) = LOWER(REPLACE(area_name, ' ', '')) THEN 1
            WHEN LOWER(u.areaname) LIKE LOWER(area_name) || '%' THEN 2
            ELSE 3
        END,
        COALESCE(safe_numeric(u.google_place_rating), 0::NUMERIC) DESC,
        COALESCE(safe_numeric(u.price_per_sft), 0::NUMERIC) DESC
    LIMIT 200;
END;
$$;

-- =====================================================
-- Function 6: Get single property by ID
-- Endpoint: /api/v1/properties/{property_id}
-- =====================================================
CREATE OR REPLACE FUNCTION get_property_by_id_func(prop_id INT)
RETURNS TABLE (
    id INT,
    projectname TEXT,
    buildername TEXT,
    project_type TEXT,
    bhk TEXT,
    sqfeet TEXT,
    price_per_sft FLOAT,
    construction_status TEXT,
    areaname TEXT,
    images TEXT,
    full_details JSONB
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
        u.project_type::TEXT,
        u.bhk::TEXT,
        u.sqfeet::TEXT,
        safe_numeric(u.price_per_sft)::FLOAT,
        u.construction_status::TEXT,
        u.areaname::TEXT,
        u.images::TEXT,
        -- Full details as JSONB (split into smaller objects to avoid 100-arg limit)
        jsonb_build_object(
            'id', u.id,
            'projectname', u.projectname,
            'buildername', u.buildername,
            'project_type', u.project_type,
            'bhk', u.bhk,
            'sqfeet', u.sqfeet,
            'price_per_sft', safe_numeric(u.price_per_sft),
            'construction_status', u.construction_status,
            'areaname', u.areaname
        ) || jsonb_build_object(
            'images', u.images,
            'communitytype', u.communitytype,
            'status', u.status,
            'project_status', u.project_status,
            'isavailable', u.isavailable,
            'projectlocation', u.projectlocation,
            'google_place_name', u.google_place_name,
            'google_place_address', u.google_place_address,
            'google_maps_location', u.google_maps_location,
            'mobile_google_map_url', u.mobile_google_map_url
        ) || jsonb_build_object(
            'baseprojectprice', safe_numeric(u.baseprojectprice),
            'price_per_sft', safe_numeric(u.price_per_sft),
            'total_buildup_area', u.total_buildup_area,
            'price_per_sft_update_date', u.price_per_sft_update_date,
            'floor_rise_charges', u.floor_rise_charges,
            'floor_rise_amount_per_floor', u.floor_rise_amount_per_floor,
            'floor_rise_applicable_above_floor_no', u.floor_rise_applicable_above_floor_no,
            'facing_charges', u.facing_charges,
            'preferential_location_charges', u.preferential_location_charges,
            'preferential_location_charges_conditions', u.preferential_location_charges_conditions
        ) || jsonb_build_object(
            'amount_for_extra_car_parking', u.amount_for_extra_car_parking,
            'project_launch_date', u.project_launch_date,
            'possession_date', u.possession_date,
            'construction_status', u.construction_status,
            'construction_material', u.construction_material,
            'total_land_area', u.total_land_area,
            'number_of_towers', u.number_of_towers,
            'number_of_floors', u.number_of_floors,
            'number_of_flats_per_floor', u.number_of_flats_per_floor,
            'total_number_of_units', u.total_number_of_units
        ) || jsonb_build_object(
            'open_space', u.open_space,
            'carpet_area_percentage', u.carpet_area_percentage,
            'floor_to_ceiling_height', u.floor_to_ceiling_height,
            'bhk', u.bhk,
            'sqfeet', u.sqfeet,
            'sqyard', u.sqyard,
            'facing', u.facing,
            'no_of_car_parkings', u.no_of_car_parkings,
            'external_amenities', u.external_amenities,
            'specification', u.specification
        ) || jsonb_build_object(
            'powerbackup', u.powerbackup,
            'no_of_passenger_lift', u.no_of_passenger_lift,
            'no_of_service_lift', u.no_of_service_lift,
            'visitor_parking', u.visitor_parking,
            'ground_vehicle_movement', u.ground_vehicle_movement,
            'main_door_height', u.main_door_height,
            'home_loan', u.home_loan,
            'available_banks_for_loan', u.available_banks_for_loan,
            'builder_age', u.builder_age,
            'builder_completed_properties', u.builder_completed_properties
        ) || jsonb_build_object(
            'builder_ongoing_projects', u.builder_ongoing_projects,
            'builder_upcoming_properties', u.builder_upcoming_properties,
            'builder_total_properties', u.builder_total_properties,
            'builder_operating_locations', u.builder_operating_locations,
            'builder_origin_city', u.builder_origin_city,
            'poc_name', u.poc_name,
            'poc_contact', u.poc_contact,
            'poc_role', u.poc_role,
            'alternative_contact', u.alternative_contact,
            'useremail', u.useremail
        ) || jsonb_build_object(
            'google_place_rating', safe_numeric(u.google_place_rating),
            'google_place_user_ratings_total', u.google_place_user_ratings_total,
            'rera_number', u.rera_number,
            'projectbrochure', u.projectbrochure
        )
    FROM "unified_data_DataType_Raghu" u
    WHERE u.id = prop_id;
END;
$$;

-- =====================================================
-- Grant execute permissions to anon role
-- =====================================================
GRANT EXECUTE ON FUNCTION safe_numeric(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION safe_numeric(INTEGER) TO anon;
GRANT EXECUTE ON FUNCTION safe_numeric(BIGINT) TO anon;
GRANT EXECUTE ON FUNCTION get_all_insights() TO anon;
GRANT EXECUTE ON FUNCTION search_locations_func(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION get_location_trends_func(INT) TO anon;
GRANT EXECUTE ON FUNCTION get_property_costs_func(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION get_properties_func(TEXT, TEXT) TO anon;
GRANT EXECUTE ON FUNCTION get_property_by_id_func(INT) TO anon;

-- =====================================================
-- NOTES:
-- =====================================================
-- 1. These functions are READ-ONLY and safe for anon access
-- 2. They replicate the exact logic from api.py endpoints
-- 3. Summary fields (sentiment_summary, growth_summary, invest_summary) 
--    are fetched from location_insights table
-- 4. All functions use SECURITY DEFINER to run with elevated privileges
-- 5. The amenities endpoint (/api/v1/location/{id}/amenities/{type}) 
--    uses Google Places API and cannot be replicated in SQL
-- 6. After running this file, you can call these functions via Supabase REST API:
--    - POST https://your-project.supabase.co/rest/v1/rpc/get_all_insights
--    - POST https://your-project.supabase.co/rest/v1/rpc/search_locations_func
--      with body: {"search_query": "gachibowli"}
--    - POST https://your-project.supabase.co/rest/v1/rpc/get_location_trends_func
--      with body: {"loc_id": 123}
--    - POST https://your-project.supabase.co/rest/v1/rpc/get_property_costs_func
--      with body: {"area_name": "Gachibowli"}
--    - POST https://your-project.supabase.co/rest/v1/rpc/get_properties_func
--      with body: {"area_name": "Gachibowli", "bhk_filter": "2"}
--    - POST https://your-project.supabase.co/rest/v1/rpc/get_property_by_id_func
--      with body: {"prop_id": 123}
-- =====================================================
