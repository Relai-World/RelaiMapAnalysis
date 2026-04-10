-- Check all variations of Rajini/Rajaji nagar
SELECT id, name 
FROM locations 
WHERE name ILIKE '%rajini%' 
   OR name ILIKE '%rajaji%'
   OR name ILIKE '%rajaj%'
ORDER BY name;
