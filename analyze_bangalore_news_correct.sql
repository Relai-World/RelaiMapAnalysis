-- =====================================================
-- ANALYZE BANGALORE NEWS DATA (CORRECT COLUMNS)
-- =====================================================

-- 1. Total count and date range
SELECT 
    COUNT(*) as total_articles,
    MIN(published_at) as earliest_date,
    MAX(published_at) as latest_date,
    COUNT(DISTINCT location_id) as unique_locations,
    COUNT(DISTINCT source) as unique_sources
FROM bangalore_news_scraper;

-- 2. Articles per location
SELECT 
    location_name,
    COUNT(*) as article_count,
    MIN(published_at) as earliest_article,
    MAX(published_at) as latest_article,
    ROUND(AVG(sentiment_score)::NUMERIC, 3) as avg_sentiment
FROM bangalore_news_scraper
GROUP BY location_name
ORDER BY article_count DESC
LIMIT 20;

-- 3. Sentiment distribution
SELECT 
    sentiment_label,
    COUNT(*) as count,
    ROUND(AVG(sentiment_score)::NUMERIC, 3) as avg_score,
    ROUND(AVG(confidence)::NUMERIC, 3) as avg_confidence
FROM bangalore_news_scraper
GROUP BY sentiment_label
ORDER BY count DESC;

-- 4. Articles by source
SELECT 
    source,
    COUNT(*) as article_count,
    ROUND(AVG(sentiment_score)::NUMERIC, 3) as avg_sentiment
FROM bangalore_news_scraper
GROUP BY source
ORDER BY article_count DESC;

-- 5. Articles by category
SELECT 
    category,
    COUNT(*) as article_count
FROM bangalore_news_scraper
GROUP BY category
ORDER BY article_count DESC;

-- 6. Articles without location mapping
SELECT 
    COUNT(*) as articles_without_location
FROM bangalore_news_scraper
WHERE location_id IS NULL;

-- 7. Recent articles (last 30 days)
SELECT 
    location_name,
    LEFT(content, 100) as content_preview,
    published_at,
    sentiment_label,
    ROUND(sentiment_score::NUMERIC, 2) as sentiment
FROM bangalore_news_scraper
WHERE published_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY published_at DESC
LIMIT 20;

-- 8. Data quality check
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END) as missing_content,
    COUNT(CASE WHEN published_at IS NULL THEN 1 END) as missing_date,
    COUNT(CASE WHEN location_id IS NULL THEN 1 END) as missing_location,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as missing_sentiment,
    COUNT(CASE WHEN source IS NULL OR source = '' THEN 1 END) as missing_source
FROM bangalore_news_scraper;

-- 9. Sentiment by location (top 10)
SELECT 
    location_name,
    COUNT(*) as articles,
    ROUND(AVG(sentiment_score)::NUMERIC, 3) as avg_sentiment,
    COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
    COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral,
    COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative
FROM bangalore_news_scraper
GROUP BY location_name
HAVING COUNT(*) > 5
ORDER BY articles DESC
LIMIT 10;

-- 10. Check for duplicate URLs
SELECT 
    url,
    COUNT(*) as count
FROM bangalore_news_scraper
GROUP BY url
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 10;
