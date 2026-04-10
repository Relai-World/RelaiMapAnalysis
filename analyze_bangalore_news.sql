-- =====================================================
-- ANALYZE BANGALORE NEWS DATA
-- Detailed analysis of bangalore_news_scraper table
-- =====================================================

-- 1. Table structure - see what columns exist
SELECT 'Checking table structure...' as analysis;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'bangalore_news_scraper'
ORDER BY ordinal_position;

-- 2. Sample data to see actual structure
SELECT 'Sample data:' as analysis;
SELECT * FROM bangalore_news_scraper LIMIT 3;

-- 2. Total count and date range
SELECT 
    'Data overview:' as analysis,
    COUNT(*) as total_articles,
    MIN(published_at) as earliest_date,
    MAX(published_at) as latest_date,
    COUNT(DISTINCT location_id) as unique_locations
FROM bangalore_news_scraper;

-- 3. Articles per location
SELECT 
    l.name as location_name,
    COUNT(bns.id) as article_count,
    MIN(bns.published_at) as earliest_article,
    MAX(bns.published_at) as latest_article
FROM bangalore_news_scraper bns
LEFT JOIN locations l ON l.id = bns.location_id
GROUP BY l.name
ORDER BY article_count DESC
LIMIT 20;

-- 4. Sentiment distribution
SELECT 
    'Sentiment distribution:' as analysis,
    COUNT(CASE WHEN sentiment_score > 0.6 THEN 1 END) as positive_articles,
    COUNT(CASE WHEN sentiment_score BETWEEN 0.4 AND 0.6 THEN 1 END) as neutral_articles,
    COUNT(CASE WHEN sentiment_score < 0.4 THEN 1 END) as negative_articles,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as no_sentiment,
    ROUND(AVG(sentiment_score)::NUMERIC, 3) as avg_sentiment
FROM bangalore_news_scraper;

-- 5. Articles without location mapping
SELECT 
    'Articles without location:' as analysis,
    COUNT(*) as count
FROM bangalore_news_scraper
WHERE location_id IS NULL;

-- 6. Sample articles without location
SELECT id, title, LEFT(content, 100) as content_preview
FROM bangalore_news_scraper
WHERE location_id IS NULL
LIMIT 10;

-- 7. Articles by source
SELECT 
    source,
    COUNT(*) as article_count
FROM bangalore_news_scraper
GROUP BY source
ORDER BY article_count DESC;

-- 8. Recent articles (last 30 days)
SELECT 
    l.name as location,
    bns.title,
    bns.published_at,
    ROUND(bns.sentiment_score::NUMERIC, 2) as sentiment
FROM bangalore_news_scraper bns
LEFT JOIN locations l ON l.id = bns.location_id
WHERE bns.published_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY bns.published_at DESC
LIMIT 20;

-- 9. Check for duplicates
SELECT 
    title,
    COUNT(*) as count
FROM bangalore_news_scraper
GROUP BY title
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;

-- 10. Data quality check
SELECT 
    'Data quality:' as check_type,
    COUNT(*) as total,
    COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as missing_title,
    COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END) as missing_content,
    COUNT(CASE WHEN published_at IS NULL THEN 1 END) as missing_date,
    COUNT(CASE WHEN location_id IS NULL THEN 1 END) as missing_location,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as missing_sentiment
FROM bangalore_news_scraper;
