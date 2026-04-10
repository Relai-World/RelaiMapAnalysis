-- =====================================================
-- MERGE bangalore_news_scraper INTO news_balanced_corpus_1
-- =====================================================
-- Run this in Supabase SQL Editor

-- Based on the error, the column order in news_balanced_corpus_1 is:
-- (id, location_name, source, url, content, scraped_at, location_id, published_at, category, sentiment_score, sentiment_label, confidence)

-- Step 1: Insert all articles from bangalore_news_scraper
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
    id,
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
WHERE location_id IS NOT NULL
ON CONFLICT (id) DO NOTHING;

-- Step 2: Verify the merge
SELECT 'Total articles in news_balanced_corpus_1:' as status, COUNT(*) as count
FROM news_balanced_corpus_1;

-- Step 3: Check articles without sentiment
SELECT 'Articles without sentiment:' as status, COUNT(*) as count
FROM news_balanced_corpus_1
WHERE sentiment_score IS NULL;

-- Step 4: Show sample articles
SELECT 'Sample articles:' as status;
SELECT id, location_id, source, LEFT(content, 50) as content_preview, sentiment_score
FROM news_balanced_corpus_1
LIMIT 5;

-- Step 2: Verify the merge
SELECT 'Total articles in news_balanced_corpus_1:' as status, COUNT(*) as count
FROM news_balanced_corpus_1;

-- Step 3: Check articles without sentiment
SELECT 'Articles without sentiment:' as status, COUNT(*) as count
FROM news_balanced_corpus_1
WHERE sentiment_score IS NULL;

-- Step 4: Show sample articles
SELECT 'Sample articles:' as status;
SELECT id, location_id, source, LEFT(content, 50) as content_preview, sentiment_score
FROM news_balanced_corpus_1
LIMIT 5;
