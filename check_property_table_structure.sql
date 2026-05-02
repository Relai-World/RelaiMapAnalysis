-- Check the structure of bangalore_property_costs table
SELECT 
  column_name,
  data_type,
  udt_name,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'bangalore_property_costs'
  AND column_name LIKE '%location%'
ORDER BY ordinal_position;

-- Also check a few sample records
SELECT 
  projectname,
  google_place_location,
  pg_typeof(google_place_location) as data_type
FROM bangalore_property_costs
WHERE google_place_location IS NOT NULL
LIMIT 5;
