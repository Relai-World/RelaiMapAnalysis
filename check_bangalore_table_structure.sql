-- Check what columns exist in bangalore_news_scraper
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'bangalore_news_scraper'
ORDER BY ordinal_position;

-- Sample data
SELECT * FROM bangalore_news_scraper LIMIT 2;
