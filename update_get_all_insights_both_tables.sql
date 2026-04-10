-- =====================================================
-- UPDATE get_all_insights TO USE BOTH NEWS TABLES
-- =====================================================
-- This combines sentiment from both news_balanced_corpus_1 and bangalore_news_scraper
-- Run this in Supabase SQL Editor

CREATE OR REPLACE FUNCTION get_all_insights()
RETURNS TABLE (
    location_id INT,
    location TEXT,
    longitude FLOAT,
    latitude FLOAT,
    avg_sentiment FLOAT,
    growth_score FLOAT,
    investment_score FLOAT,
    article_count INT,
    avg_property_price FLOAT,
    property_count INT,
    min_property_price FLOAT,
    max_property_price FLOAT,
    price_summary TEXT,
    sentiment_summary TEXT,
    growth_summary TEXT,
    invest_summary TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    WITH property_stats AS (
        SELECT 
            LOWER(areaname) as area_lower,
            areaname as original_area,
            COUNT(*) as property_count,
            AVG(safe_numeric(price_per_sft)) as avg_price_per_sft,
            MIN(safe_numeric(price_per_sft)) as min_price_per_sft,
            MAX(safe_numeric(price_per_sft)) as max_price_per_sft
        FROM "unified_data_DataType_Raghu" 
        WHERE safe_numeric(price_per_sft) > 0
        GROUP BY LOWER(areaname), areaname
    ),
    location_property_matches AS (
        SELECT 
            l.id as loc_id,
            l.name as loc_name,
            SUM(ps.property_count) as total_property_count,
            AVG(ps.avg_price_per_sft) as avg_price_per_sft,
            MIN(ps.min_price_per_sft) as min_price_per_sft,
            MAX(ps.max_price_per_sft) as max_price_per_sft
        FROM locations l
        LEFT JOIN property_stats ps ON (
            LOWER(TRIM(ps.original_area)) = LOWER(TRIM(l.name))
            OR LOWER(REPLACE(TRIM(ps.original_area), ' ', '')) = LOWER(REPLACE(TRIM(l.name), ' ', ''))
            OR TRIM(ps.original_area) ILIKE TRIM(l.name)
            OR TRIM(l.name) ILIKE TRIM(ps.original_area)
        )
        GROUP BY l.id, l.name
    ),
    -- Combine articles from BOTH tables
    combined_articles AS (
        SELECT 
            nbc.location_id,
            nbc.sentiment_score
        FROM news_balanced_corpus_1 nbc
        WHERE nbc.sentiment_score IS NOT NULL
        
        UNION ALL
        
        SELECT 
            bns.location_id,
            bns.sentiment_score
        FROM bangalore_news_scraper bns
        WHERE bns.sentiment_score IS NOT NULL
    ),
    article_stats AS (
        SELECT 
            ca.location_id as art_loc_id,
            COUNT(*) as article_count,
            AVG(ca.sentiment_score) as avg_sentiment_score
        FROM combined_articles ca
        GROUP BY ca.location_id
    )
    SELECT
        l.id::INT,
        l.name::TEXT,
        -- Parse POINT(x y) format manually
        CASE 
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 1) AS FLOAT)
            ELSE NULL
        END,
        CASE 
            WHEN l.geom LIKE 'POINT(%' THEN
                CAST(SPLIT_PART(REPLACE(REPLACE(l.geom, 'POINT(', ''), ')', ''), ' ', 2) AS FLOAT)
            ELSE NULL
        END,
        COALESCE(a.avg_sentiment_score, COALESCE(li.avg_sentiment_score, 0))::FLOAT,
        COALESCE(li.growth_score, 0)::FLOAT,
        COALESCE(li.investment_score, 0)::FLOAT,
        COALESCE(a.article_count, 0)::INT,
        COALESCE(lpm.avg_price_per_sft, 0)::FLOAT,
        COALESCE(lpm.total_property_count, 0)::INT,
        COALESCE(lpm.min_price_per_sft, 0)::FLOAT,
        COALESCE(lpm.max_price_per_sft, 0)::FLOAT,
        -- Generate price summary
        CASE 
            WHEN COALESCE(lpm.total_property_count, 0) > 0 THEN
                CASE 
                    WHEN COALESCE(lpm.min_price_per_sft, 0) = COALESCE(lpm.max_price_per_sft, 0) THEN
                        'Properties priced at ₹' || ROUND(COALESCE(lpm.avg_price_per_sft, 0))::TEXT || '/sqft (' || COALESCE(lpm.total_property_count, 0)::TEXT || ' properties available)'
                    ELSE
                        'Properties range from ₹' || ROUND(COALESCE(lpm.min_price_per_sft, 0))::TEXT || ' to ₹' || ROUND(COALESCE(lpm.max_price_per_sft, 0))::TEXT || '/sqft (avg ₹' || ROUND(COALESCE(lpm.avg_price_per_sft, 0))::TEXT || '/sqft, ' || COALESCE(lpm.total_property_count, 0)::TEXT || ' properties)'
                END
            ELSE 'No property pricing data available'
        END::TEXT,
        COALESCE(li.sentiment_summary, 'Sentiment is stable across major news outlets.')::TEXT,
        COALESCE(li.growth_summary, 'Infrastructure is developing steadily.')::TEXT,
        COALESCE(li.invest_summary, 'Prices show consistent long-term appreciation.')::TEXT
    FROM locations l
    LEFT JOIN location_insights li ON li.location_id = l.id
    LEFT JOIN location_property_matches lpm ON lpm.loc_id = l.id
    LEFT JOIN article_stats a ON a.art_loc_id = l.id
    ORDER BY l.id;
END;
$$;

-- Grant permissions
GRANT EXECUTE ON FUNCTION get_all_insights() TO anon;
GRANT EXECUTE ON FUNCTION get_all_insights() TO authenticated;

-- Test the function
SELECT 'Testing updated function:' as status;
SELECT location_id, location, avg_sentiment, article_count
FROM get_all_insights()
WHERE article_count > 0
ORDER BY article_count DESC
LIMIT 10;
