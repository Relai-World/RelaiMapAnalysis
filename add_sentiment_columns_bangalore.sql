-- =====================================================
-- ADD SENTIMENT COLUMNS TO bangalore_news_scraper
-- =====================================================
-- Run this in Supabase SQL Editor

-- Add sentiment_score column (FLOAT, nullable)
ALTER TABLE bangalore_news_scraper 
ADD COLUMN IF NOT EXISTS sentiment_score FLOAT;

-- Add sentiment_label column (TEXT, nullable)
ALTER TABLE bangalore_news_scraper 
ADD COLUMN IF NOT EXISTS sentiment_label TEXT;

-- Add confidence column (FLOAT, nullable)
ALTER TABLE bangalore_news_scraper 
ADD COLUMN IF NOT EXISTS confidence FLOAT;

-- Verify the columns were added
SELECT 'Columns added successfully!' as status;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'bangalore_news_scraper'
AND column_name IN ('sentiment_score', 'sentiment_label', 'confidence')
ORDER BY column_name;

-- Check how many articles need sentiment analysis
SELECT 'Articles needing sentiment:' as status, COUNT(*) as count
FROM bangalore_news_scraper
WHERE sentiment_score IS NULL;
