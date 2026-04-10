-- =====================================================
-- DELETE BOVIPALYA FROM ALL TABLES
-- Removes Bovipalya location and all related data
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================

-- First, check what will be deleted
SELECT 'Checking Bovipalya data before deletion...' as status;

-- Check locations table
SELECT 'Locations table:' as table_name, id, name 
FROM locations 
WHERE name ILIKE '%Bovipalya%';

-- Check location_insights table
SELECT 'Location insights table:' as table_name, location_id 
FROM location_insights li
JOIN locations l ON l.id = li.location_id
WHERE l.name ILIKE '%Bovipalya%';

-- Check news tables (if any references exist)
SELECT 'News table (Hyderabad):' as table_name, COUNT(*) as count
FROM news_balanced_corpus_1 
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%Bovipalya%');

SELECT 'News table (Bangalore):' as table_name, COUNT(*) as count
FROM bangalore_news_articles 
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%Bovipalya%');

-- Now delete (uncomment these lines after reviewing the check results above)

-- Delete from location_insights first (foreign key constraint)
DELETE FROM location_insights 
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%Bovipalya%');

-- Delete from news tables if needed
DELETE FROM news_balanced_corpus_1 
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%Bovipalya%');

DELETE FROM bangalore_news_articles 
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%Bovipalya%');

-- Finally delete from locations table
DELETE FROM locations 
WHERE name ILIKE '%Bovipalya%';

-- Verify deletion
SELECT 'Verification - should return 0 rows:' as status;
SELECT COUNT(*) as remaining_bovipalya_locations FROM locations WHERE name ILIKE '%Bovipalya%';

SELECT '✅ Bovipalya deleted from all tables!' as status;
