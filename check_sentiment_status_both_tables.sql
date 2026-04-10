-- =====================================================
-- CHECK SENTIMENT STATUS FOR BOTH TABLES
-- =====================================================
-- Run this in Supabase SQL Editor

-- 1. Check news_balanced_corpus_1 (Hyderabad)
SELECT 'news_balanced_corpus_1 (Hyderabad)' as table_name;
SELECT 
    COUNT(*) as total_articles,
    COUNT(sentiment_score) as with_sentiment,
    COUNT(*) - COUNT(sentiment_score) as without_sentiment,
    ROUND(COUNT(sentiment_score)::numeric / COUNT(*)::numeric * 100, 2) as completion_percentage
FROM news_balanced_corpus_1;

-- 2. Check bangalore_news_scraper (Bangalore)
SELECT 'bangalore_news_scraper (Bangalore)' as table_name;
SELECT 
    COUNT(*) as total_articles,
    COUNT(sentiment_score) as with_sentiment,
    COUNT(*) - COUNT(sentiment_score) as without_sentiment,
    ROUND(COUNT(sentiment_score)::numeric / COUNT(*)::numeric * 100, 2) as completion_percentage
FROM bangalore_news_scraper;

-- 3. Combined summary
SELECT 'COMBINED SUMMARY' as status;
SELECT 
    'Total' as metric,
    (SELECT COUNT(*) FROM news_balanced_corpus_1) + (SELECT COUNT(*) FROM bangalore_news_scraper) as total_articles,
    (SELECT COUNT(sentiment_score) FROM news_balanced_corpus_1) + (SELECT COUNT(sentiment_score) FROM bangalore_news_scraper) as with_sentiment,
    ((SELECT COUNT(*) FROM news_balanced_corpus_1) + (SELECT COUNT(*) FROM bangalore_news_scraper)) - 
    ((SELECT COUNT(sentiment_score) FROM news_balanced_corpus_1) + (SELECT COUNT(sentiment_score) FROM bangalore_news_scraper)) as without_sentiment;

-- 4. Sample articles without sentiment from each table
SELECT 'Articles WITHOUT sentiment - news_balanced_corpus_1:' as status;
SELECT id, location_id, source, LEFT(content, 50) as content_preview
FROM news_balanced_corpus_1
WHERE sentiment_score IS NULL
LIMIT 5;

SELECT 'Articles WITHOUT sentiment - bangalore_news_scraper:' as status;
SELECT id, location_id, source, LEFT(content, 50) as content_preview
FROM bangalore_news_scraper
WHERE sentiment_score IS NULL
LIMIT 5;
