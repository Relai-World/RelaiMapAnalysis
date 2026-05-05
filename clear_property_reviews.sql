-- Clear existing property reviews so they get regenerated with improved prompt
-- Run this in Supabase SQL Editor

UPDATE "unified_data_DataType_Raghu"
SET "Property_Review" = NULL
WHERE "Property_Review" IS NOT NULL;

-- Verify the update
SELECT COUNT(*) as cleared_reviews
FROM "unified_data_DataType_Raghu"
WHERE "Property_Review" IS NULL;
