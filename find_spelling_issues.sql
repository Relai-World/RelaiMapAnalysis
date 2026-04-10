-- =====================================================
-- FIND SPELLING ISSUES IN LOCATION NAMES
-- Identifies duplicates, similar names, and inconsistencies
-- =====================================================

-- 1. Find exact duplicates (case-insensitive)
SELECT 
    LOWER(name) as normalized_name,
    COUNT(*) as count,
    STRING_AGG(name, ' | ') as variations,
    STRING_AGG(id::TEXT, ', ') as ids
FROM locations
GROUP BY LOWER(name)
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- 2. Find locations with similar names (differ by spaces, hyphens, etc)
SELECT 
    REPLACE(REPLACE(LOWER(name), ' ', ''), '-', '') as normalized,
    COUNT(*) as count,
    STRING_AGG(name, ' | ') as variations,
    STRING_AGG(id::TEXT, ', ') as ids
FROM locations
GROUP BY REPLACE(REPLACE(LOWER(name), ' ', ''), '-', '')
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- 3. Find locations with trailing/leading spaces
SELECT id, name, LENGTH(name) as len, LENGTH(TRIM(name)) as trimmed_len
FROM locations
WHERE LENGTH(name) != LENGTH(TRIM(name));

-- 4. Find locations with unusual characters
SELECT id, name
FROM locations
WHERE name ~ '[^a-zA-Z0-9 \-]'  -- Contains characters other than letters, numbers, spaces, hyphens
ORDER BY name;

-- 5. List all location names sorted alphabetically to spot issues manually
SELECT id, name, 
    CASE 
        WHEN name LIKE '% %' THEN 'Has space'
        WHEN name LIKE '%-%' THEN 'Has hyphen'
        ELSE 'Simple'
    END as name_type
FROM locations
ORDER BY name;

-- 6. Find potential misspellings (names that are very similar)
-- This uses Levenshtein distance if you have the fuzzystrmatch extension
-- If not available, skip this query
-- CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
-- SELECT 
--     l1.id as id1, l1.name as name1,
--     l2.id as id2, l2.name as name2,
--     levenshtein(LOWER(l1.name), LOWER(l2.name)) as distance
-- FROM locations l1
-- CROSS JOIN locations l2
-- WHERE l1.id < l2.id
--     AND levenshtein(LOWER(l1.name), LOWER(l2.name)) BETWEEN 1 AND 3
-- ORDER BY distance, l1.name;
