-- =====================================================
-- CHECK SCHEMAS OF BOTH TABLES
-- =====================================================
-- Run this in Supabase SQL Editor to see the exact schemas

-- Check bangalore_news_scraper structure
SELECT 
    column_name, 
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'bangalore_news_scraper'
ORDER BY ordinal_position;

-- Check news_balanced_corpus_1 structure
SELECT 
    column_name, 
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'news_balanced_corpus_1'
ORDER BY ordinal_position;

-- Check if id has a sequence
SELECT 
    table_name,
    column_name,
    column_default
FROM information_schema.columns
WHERE table_name IN ('bangalore_news_scraper', 'news_balanced_corpus_1')
AND column_name = 'id';
