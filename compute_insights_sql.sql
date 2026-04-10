-- =====================================================
-- COMPUTE LOCATION INSIGHTS FOR ALL LOCATIONS
-- Combines data from both news_balanced_corpus_1 and bangalore_news_scraper
-- =====================================================
-- Run this in Supabase SQL Editor

-- Create or replace the compute function
CREATE OR REPLACE FUNCTION compute_location_insights()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    loc RECORD;
    article_cnt INTEGER;
    avg_sent FLOAT;
    avg_conf FLOAT;
    growth FLOAT;
    invest FLOAT;
    buzz FLOAT;
    sent_norm FLOAT;
BEGIN
    -- Loop through all locations
    FOR loc IN SELECT id FROM locations LOOP
        
        -- Get combined sentiment data from both tables
        SELECT 
            COUNT(*) as cnt,
            AVG(sentiment_score) as sent,
            AVG(confidence) as conf
        INTO article_cnt, avg_sent, avg_conf
        FROM (
            SELECT sentiment_score, confidence
            FROM news_balanced_corpus_1
            WHERE location_id = loc.id AND sentiment_score IS NOT NULL
            
            UNION ALL
            
            SELECT sentiment_score, confidence
            FROM bangalore_news_scraper
            WHERE location_id = loc.id AND sentiment_score IS NOT NULL
        ) combined;
        
        -- Default values if no articles
        article_cnt := COALESCE(article_cnt, 0);
        avg_sent := COALESCE(avg_sent, 0.0);
        avg_conf := COALESCE(avg_conf, 0.0);
        
        -- Calculate growth score
        IF article_cnt = 0 THEN
            growth := 0.0;
        ELSE
            -- Buzz score (logarithmic)
            buzz := LOG(10, article_cnt + 1) / 3.5;
            buzz := LEAST(GREATEST(buzz, 0.0), 1.0);
            
            -- Sentiment normalized
            sent_norm := LEAST(GREATEST(avg_sent + 0.5, 0.0), 1.0);
            
            -- Growth = 80% buzz + 20% sentiment
            growth := (0.8 * buzz) + (0.2 * sent_norm);
            
            -- Boost for high volume
            IF article_cnt > 500 THEN
                growth := growth * 1.2;
            END IF;
            
            growth := LEAST(GREATEST(growth, 0.0), 1.0);
        END IF;
        
        -- Calculate investment score
        sent_norm := LEAST(GREATEST(avg_sent + 0.5, 0.0), 1.0);
        invest := (0.7 * growth) + (0.3 * sent_norm);
        invest := LEAST(GREATEST(invest, 0.0), 1.0);
        
        -- Upsert into location_insights
        -- First try to update
        UPDATE location_insights
        SET 
            avg_sentiment_score = avg_sent,
            growth_score = growth,
            investment_score = invest,
            last_updated = NOW()
        WHERE location_id = loc.id;
        
        -- If no rows updated, insert new
        IF NOT FOUND THEN
            INSERT INTO location_insights (
                location_id,
                avg_sentiment_score,
                growth_score,
                investment_score,
                last_updated
            )
            VALUES (
                loc.id,
                avg_sent,
                growth,
                invest,
                NOW()
            );
        END IF;
        
    END LOOP;
    
    RAISE NOTICE 'Location insights computed successfully';
END;
$$;

-- Execute the function
SELECT compute_location_insights();

-- Verify results
SELECT 'Total insights computed:' as status, COUNT(*) as count
FROM location_insights;

SELECT 'Breakdown by city:' as status;
SELECT 
    l.city,
    COUNT(*) as count,
    ROUND(AVG(li.growth_score)::numeric, 3) as avg_growth,
    ROUND(AVG(li.investment_score)::numeric, 3) as avg_investment
FROM location_insights li
JOIN locations l ON l.id = li.location_id
GROUP BY l.city;
