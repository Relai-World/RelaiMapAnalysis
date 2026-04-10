-- =====================================================
-- DELETE DUPLICATE BANGALORE LOCATIONS
-- Run this in Supabase SQL Editor
-- =====================================================

-- Delete 21 duplicate/extra Bangalore locations
-- These are NOT in the unique list provided

DELETE FROM locations WHERE id IN (
    71,   -- Chikagubbi (duplicate of 302 Chikkagubbi)
    205,  -- Sai Baba Ashram Road (not in unique list)
    277,  -- Baglur (duplicate of 49 Bagalur)
    285,  -- Bendiganahalli (not in unique list)
    291,  -- Bommenahalli village (duplicate of 290 Bommenahalli)
    324,  -- Hennur Road (duplicate of 101 Hennur / 323 Hennur Main Road)
    325,  -- Honnenahalli (not in unique list)
    329,  -- Huvinayakanahalli (not in unique list)
    331,  -- JP Nagar Phase 7 (duplicate of 111 JP Nagar)
    350,  -- Koralur (not in unique list)
    352,  -- Krishnarajapuram (duplicate of 351 Krishnarajapura)
    355,  -- Kurubarakunte (not in unique list)
    359,  -- Madiwala (duplicate of 358 Madiwala)
    370,  -- Nagegowdanapalya (not in unique list)
    372,  -- Neraganahalli (not in unique list)
    385,  -- Sarjapur (duplicate of 209 Sarjapur)
    386,  -- SHIVAJINAGAR (not in unique list)
    390,  -- Sahakara Nagar (duplicate of 389 Sahakar Nagar)
    404,  -- Upparahalli (not in unique list)
    411,  -- Vijayanagara (duplicate of 410 Vijayanagar)
    412   -- Yelahanka (duplicate of 240 Yelahanka)
) AND city = 'Bangalore';

-- Verify the deletion
SELECT 'After deletion - Bangalore locations count:' as status, COUNT(*) as count
FROM locations
WHERE city = 'Bangalore';

-- Show the deleted IDs (should return 0 rows)
SELECT 'Checking deleted IDs (should be empty):' as status;
SELECT id, name FROM locations 
WHERE id IN (71, 205, 277, 285, 291, 324, 325, 329, 331, 350, 352, 355, 359, 370, 372, 385, 386, 390, 404, 411, 412)
AND city = 'Bangalore';
