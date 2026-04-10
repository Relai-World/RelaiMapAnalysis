-- =====================================================
-- DEBUG MERGE ISSUE
-- =====================================================
-- Run this in Supabase SQL Editor to find the problem

-- 1. Check if bangalore_news_scraper has data
SELECT 'bangalore_news_scraper count:' as status, COUNT(*) as count
FROM bangalore_news_scraper;

-- 2. Check sample IDs from bangalore_news_scraper
SELECT 'Sample IDs from bangalore_news_scraper:' as status;
SELECT id, location_id, source
FROM bangalore_news_scraper
LIMIT 5;

-- 3. Check if those IDs already exist in news_balanced_corpus_1
SELECT 'Checking if IDs overlap:' as status;
SELECT COUNT(*) as overlapping_ids
FROM bangalore_news_scraper bns
WHERE EXISTS (
    SELECT 1 FROM news_balanced_corpus_1 nbc
    WHERE nbc.id = bns.id
);

-- 4. Check ID ranges
SELECT 'ID ranges:' as status;
SELECT 
    'bangalore_news_scraper' as table_name,
    MIN(id) as min_id,
    MAX(id) as max_id,
    COUNT(*) as total
FROM bangalore_news_scraper
UNION ALL
SELECT 
    'news_balanced_corpus_1' as table_name,
    MIN(id) as min_id,
    MAX(id) as max_id,
    COUNT(*) as total
FROM news_balanced_corpus_1;

-- 5. Try a test insert with just 1 record
-- (Comment this out after checking)
/*
INSERT INTO news_balanced_corpus_1 (
    id,
    location_id,
    location_name,
    source,
    url,
    content,
    published_at,
    category,
    scraped_at,
    sentiment_score,
    sentiment_label,
    confidence
)
SELECT 
    id + 100000 as id,  -- Offset ID to avoid conflicts
    location_id,
    location_name,
    source,
    url,
    content,
    published_at::timestamp,
    category,
    scraped_at::timestamp,
    NULL as sentiment_score,
    NULL as sentiment_label,
    NULL as confidence
FROM bangalore_news_scraper
LIMIT 1;
*/
