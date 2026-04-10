-- =====================================================
-- CHECK LOCATION_INSIGHTS TABLE
-- =====================================================
-- Run this in Supabase SQL Editor

-- 1. Total count
SELECT 'Total location insights:' as status, COUNT(*) as count
FROM location_insights;

-- 2. Breakdown by city
SELECT 'Breakdown by city:' as status;
SELECT 
    l.city,
    COUNT(*) as locations_with_insights
FROM location_insights li
JOIN locations l ON l.id = li.location_id
GROUP BY l.city;

-- 3. Sample Bangalore insights
SELECT 'Sample Bangalore insights:' as status;
SELECT 
    li.location_id,
    l.name,
    l.city,
    li.avg_sentiment_score,
    li.growth_score,
    li.investment_score,
    li.last_updated
FROM location_insights li
JOIN locations l ON l.id = li.location_id
WHERE l.city = 'Bangalore'
ORDER BY li.growth_score DESC
LIMIT 10;

-- 4. Bangalore locations WITHOUT insights
SELECT 'Bangalore locations WITHOUT insights:' as status;
SELECT 
    l.id,
    l.name,
    l.city
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id
WHERE l.city = 'Bangalore'
AND li.location_id IS NULL
LIMIT 10;

-- 5. Check if any Bangalore location has articles
SELECT 'Bangalore locations with articles:' as status;
SELECT 
    l.id,
    l.name,
    COUNT(bns.id) as article_count
FROM locations l
JOIN bangalore_news_scraper bns ON bns.location_id = l.id
WHERE l.city = 'Bangalore'
GROUP BY l.id, l.name
ORDER BY article_count DESC
LIMIT 10;
