-- =====================================================
-- FIX PEERANCHERU SPELLING MISMATCH
-- Run this in Supabase SQL Editor
-- =====================================================

-- Step 1: Check current state
SELECT 'BEFORE UPDATE:' as status;

-- Check locations table
SELECT id, name FROM locations WHERE name ILIKE '%peer%' AND name NOT ILIKE '%peerzadiguda%';

-- Check properties with different spellings
SELECT areaname, COUNT(*) as property_count 
FROM "unified_data_DataType_Raghu" 
WHERE areaname ILIKE '%peeramcher%' OR areaname ILIKE '%peeranchuru%'
GROUP BY areaname;

-- Step 2: Update locations table - Change "Peerancheru" to "Peeramcheruvu"
UPDATE locations 
SET name = 'Peeramcheruvu'
WHERE name = 'Peerancheru';

-- Step 4: Verify the fix
SELECT 'AFTER UPDATE:' as status;

-- Check updated location
SELECT id, name FROM locations WHERE name = 'Peeramcheruvu';

-- Check if properties will now match
SELECT areaname, COUNT(*) as property_count 
FROM "unified_data_DataType_Raghu" 
WHERE areaname = 'Peeramcheruvu'
GROUP BY areaname;

SELECT 'Fix complete! Peerancheru renamed to Peeramcheruvu to match property data.' as result;
