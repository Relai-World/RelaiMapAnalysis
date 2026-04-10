-- =====================================================
-- MERGE bangalore_news_scraper INTO news_balanced_corpus_1
-- WITH NEW IDs TO AVOID CONFLICTS
-- =====================================================
-- Run this in Supabase SQL Editor

-- Step 1: Find the max ID in news_balanced_corpus_1
DO $$
DECLARE
    max_id INTEGER;
BEGIN
    SELECT COALESCE(MAX(id), 0) INTO max_id FROM news_balanced_corpus_1;
    RAISE NOTICE 'Max ID in news_balanced_corpus_1: %', max_id;
END $$;

-- Step 2: Insert with new sequential IDs starting after max_id
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
    (SELECT COALESCE(MAX(id), 0) FROM news_balanced_corpus_1) + ROW_NUMBER() OVER (ORDER BY bns.id) as id,
    bns.location_id,
    bns.location_name,
    bns.source,
    bns.url,
    bns.content,
    bns.published_at::timestamp,
    bns.category,
    bns.scraped_at::timestamp,
    NULL as sentiment_score,
    NULL as sentiment_label,
    NULL as confidence
FROM bangalore_news_scraper bns
WHERE bns.location_id IS NOT NULL
AND NOT EXISTS (
    -- Avoid duplicates by URL
    SELECT 1 FROM news_balanced_corpus_1 nbc
    WHERE nbc.url = bns.url
);

-- Step 3: Verify the merge
SELECT 'After merge - Total articles:' as status, COUNT(*) as count
FROM news_balanced_corpus_1;

-- Step 4: Check new articles
SELECT 'New Bangalore articles added:' as status, COUNT(*) as count
FROM news_balanced_corpus_1
WHERE location_id IN (34,45,49,51,55,57,58,60,65,74,77,78,79,82,93,100,101,105,106,108,111,112,115,120,130,131,136,169,182,183,201,209,210,212,227,235,237,240,241);

-- Step 5: Articles without sentiment
SELECT 'Articles needing sentiment:' as status, COUNT(*) as count
FROM news_balanced_corpus_1
WHERE sentiment_score IS NULL;
