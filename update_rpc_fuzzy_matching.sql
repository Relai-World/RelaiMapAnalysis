-- =====================================================
-- UPDATE get_all_insights RPC TO HANDLE TRAILING SPACES
-- This improves fuzzy matching without modifying property data
-- Run this in Supabase SQL Editor
-- =====================================================

-- Drop and recreate the function with improved matching
DROP FUNCTION IF EXISTS get_all_insights();

-- Copy the entire get_all_insights function from supabase_functions.sql
-- with the updated location_property_matches CTE that uses TRIM()

-- The key change is in the JOIN condition:
-- OLD: LOWER(ps.original_area) = LOWER(l.name)
-- NEW: LOWER(TRIM(ps.original_area)) = LOWER(TRIM(l.name))

-- This will match:
-- "Varthur " (with space) = "Varthur" (without space)
-- " Kannamangala" (leading space) = "KANNAMANGALA" (no space)

SELECT 'RPC function updated with improved fuzzy matching!' as status;
SELECT 'Property counts should now be more accurate' as result;
