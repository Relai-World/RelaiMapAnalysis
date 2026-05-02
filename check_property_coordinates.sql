-- Check how coordinates are stored in google_place_location field
SELECT 
  projectname,
  buildername,
  areaname,
  city,
  google_place_location,
  -- Try to extract coordinates in different formats
  google_place_location::jsonb->>'lat' as lat_format1,
  google_place_location::jsonb->>'lng' as lng_format1,
  google_place_location::jsonb->>'latitude' as lat_format2,
  google_place_location::jsonb->>'longitude' as lng_format2,
  -- Check if it's a geometry type
  ST_AsText(google_place_location::geometry) as geometry_format
FROM bangalore_property_costs
WHERE google_place_location IS NOT NULL
LIMIT 10;
