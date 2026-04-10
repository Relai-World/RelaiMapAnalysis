-- =====================================================
-- CHECK VIJAYANAGARA LOCATION DATA
-- =====================================================

-- 1. Find Vijayanagara in locations table
SELECT 'Vijayanagara in locations table:' as status;
SELECT id, name, city, geom
FROM locations
WHERE name ILIKE '%vijaya%'
ORDER BY name;

-- 2. Check location_insights for Vijayanagara
SELECT 'Location insights for Vijayanagara:' as status;
SELECT 
    li.location_id,
    l.name,
    li.avg_sentiment_score,
    li.growth_score,
    li.investment_score,
    li.last_updated
FROM location_insights li
JOIN locations l ON l.id = li.location_id
WHERE l.name ILIKE '%vijaya%';

-- 3. Check articles for Vijayanagara (both tables)
SELECT 'Articles in news_balanced_corpus_1:' as status;
SELECT location_id, COUNT(*) as article_count
FROM news_balanced_corpus_1
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%vijaya%')
GROUP BY location_id;

SELECT 'Articles in bangalore_news_scraper:' as status;
SELECT location_id, COUNT(*) as article_count
FROM bangalore_news_scraper
WHERE location_id IN (SELECT id FROM locations WHERE name ILIKE '%vijaya%')
GROUP BY location_id;

-- 4. Test the get_all_insights function for Vijayanagara
SELECT 'get_all_insights result for Vijayanagara:' as status;
SELECT *
FROM get_all_insights()
WHERE location ILIKE '%vijaya%';
