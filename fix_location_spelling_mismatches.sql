-- =====================================================
-- FIX LOCATION SPELLING MISMATCHES
-- Run this in Supabase SQL Editor
-- =====================================================

-- These are high-confidence fixes (>85% similarity)

-- 1. Gandimaisamma → Gandi Maisamma (54 properties, 96% similar)
UPDATE locations SET name = 'Gandi Maisamma' WHERE name = 'Gandimaisamma';

-- 2. YALAHANKA → Yelahanka (538 properties, 95% similar)
UPDATE locations SET name = 'Yelahanka' WHERE name = 'YALAHANKA';

-- 3. SARJAPURA → Sarjapur (86 properties, 94% similar)
UPDATE locations SET name = 'Sarjapur' WHERE name = 'SARJAPURA';

-- 4. Yelahanka (trailing space fix) - 40 more properties
-- Note: This might need manual verification

-- 5. Begur (trailing space fix) - 79 more properties  
-- Note: This might need manual verification

SELECT 'Location spelling fixes applied!' as status;
SELECT 'Verify the changes by running the audit script again' as next_step;
