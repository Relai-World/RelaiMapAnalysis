-- =====================================================
-- FIX PROPERTY AREANAME INCONSISTENCIES
-- Clean up trailing spaces and normalize spellings
-- Run this in Supabase SQL Editor
-- =====================================================

-- Remove trailing and leading spaces from all areanames
UPDATE "unified_data_DataType_Raghu"
SET areaname = TRIM(areaname)
WHERE areaname != TRIM(areaname);

SELECT 'Trailing/leading spaces removed from areanames' as status;

-- Check how many records were affected
SELECT COUNT(*) as records_with_spaces_fixed
FROM "unified_data_DataType_Raghu"
WHERE areaname IS NOT NULL;

SELECT 'Property areaname cleanup complete!' as result;
