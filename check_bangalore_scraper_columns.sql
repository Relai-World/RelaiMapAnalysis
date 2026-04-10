-- Check bangalore_news_scraper columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'bangalore_news_scraper'
ORDER BY ordinal_position;
