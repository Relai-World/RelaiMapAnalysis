-- =====================================================
-- DATABASE PERFORMANCE OPTIMIZATION
-- Run this in Supabase SQL Editor
-- =====================================================

-- 1. Add index on areaname for faster property searches
CREATE INDEX IF NOT EXISTS idx_unified_data_areaname 
ON "unified_data_DataType_Raghu" (LOWER(TRIM(areaname)));

-- 2. Add index on location_id for faster joins
CREATE INDEX IF NOT EXISTS idx_news_location_id 
ON news_balanced_corpus_1 (location_id);

-- 3. Add index on price_per_sft for faster aggregations
CREATE INDEX IF NOT EXISTS idx_unified_data_price 
ON "unified_data_DataType_Raghu" (price_per_sft) 
WHERE price_per_sft IS NOT NULL;

-- 4. Create materialized view for get_all_insights (CACHE)
CREATE MATERIALIZED VIEW IF NOT EXISTS location_insights_cache AS
SELECT * FROM get_all_insights();

-- 5. Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_location_insights_cache_id 
ON location_insights_cache (location_id);

-- 6. Create function to refresh cache
CREATE OR REPLACE FUNCTION refresh_location_insights_cache()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW location_insights_cache;
END;
$$ LANGUAGE plpgsql;

SELECT 'Database optimization complete!' as status;
SELECT 'Indexes created and materialized view set up' as result;
SELECT 'Run: SELECT refresh_location_insights_cache(); to update cache' as note;
