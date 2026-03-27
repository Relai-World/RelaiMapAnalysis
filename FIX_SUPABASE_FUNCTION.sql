-- =====================================================
-- FIX: Restore the working function
-- Run this immediately in Supabase SQL Editor
-- =====================================================

DROP FUNCTION IF EXISTS get_properties_func(TEXT, TEXT);

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

-- Grant permissions
GRANT EXECUTE ON FUNCTION get_properties_func(TEXT, TEXT) TO anon;

SELECT 'Function restored to original working version!' as status;
