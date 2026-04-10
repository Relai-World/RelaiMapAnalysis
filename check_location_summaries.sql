-- =====================================================
-- CHECK: Verify location summaries are in database
-- This checks if sentiment_summary, growth_summary, and invest_summary
-- are populated for locations
-- RUN THIS IN SUPABASE SQL EDITOR
-- =====================================================

-- Check which locations have summaries
SELECT 
    l.id,
    l.name as location_name,
    CASE 
        WHEN li.sentiment_summary IS NOT NULL AND li.sentiment_summary != '' 
        THEN '✅ Has summary' 
        ELSE '❌ Missing' 
    END as sentiment_status,
    CASE 
        WHEN li.growth_summary IS NOT NULL AND li.growth_summary != '' 
        THEN '✅ Has summary' 
        ELSE '❌ Missing' 
    END as growth_status,
    CASE 
        WHEN li.invest_summary IS NOT NULL AND li.invest_summary != '' 
        THEN '✅ Has summary' 
        ELSE '❌ Missing' 
    END as invest_status,
    LEFT(li.sentiment_summary, 50) as sentiment_preview,
    LEFT(li.growth_summary, 50) as growth_preview,
    LEFT(li.invest_summary, 50) as invest_preview
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id
ORDER BY l.name
LIMIT 50;

-- Count locations with and without summaries
SELECT 
    COUNT(*) as total_locations,
    COUNT(CASE WHEN li.sentiment_summary IS NOT NULL AND li.sentiment_summary != '' THEN 1 END) as has_sentiment,
    COUNT(CASE WHEN li.growth_summary IS NOT NULL AND li.growth_summary != '' THEN 1 END) as has_growth,
    COUNT(CASE WHEN li.invest_summary IS NOT NULL AND li.invest_summary != '' THEN 1 END) as has_invest
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id;

-- Show full summaries for a specific location (change 'Dollar Hills' to test)
SELECT 
    l.name as location_name,
    li.sentiment_summary,
    li.growth_summary,
    li.invest_summary
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id
WHERE l.name ILIKE '%Dollar%'
LIMIT 5;

-- Test what the frontend gets via get_all_insights function
SELECT 
    location,
    sentiment_summary,
    growth_summary,
    invest_summary
FROM get_all_insights()
WHERE location ILIKE '%Dollar%'
LIMIT 5;
