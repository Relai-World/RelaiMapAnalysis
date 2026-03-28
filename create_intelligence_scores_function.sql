-- =====================================================
-- INTELLIGENCE SCORES WITH BENCHMARKING
-- Fetches individual location scores and city-wide averages
-- =====================================================

CREATE OR REPLACE FUNCTION get_location_intelligence_scores(loc_id INT)
RETURNS TABLE (
    location_id INT,
    location_name TEXT,
    sentiment_score FLOAT,
    growth_score FLOAT,
    investment_score FLOAT,
    sentiment_percentile FLOAT,
    growth_percentile FLOAT,
    investment_percentile FLOAT,
    city_avg_sentiment FLOAT,
    city_avg_growth FLOAT,
    city_avg_investment FLOAT,
    total_locations INT,
    sentiment_label TEXT,
    growth_label TEXT,
    investment_label TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_location_name TEXT;
    v_sentiment_score FLOAT;
    v_growth_score FLOAT;
    v_investment_score FLOAT;
    v_sentiment_percentile FLOAT;
    v_growth_percentile FLOAT;
    v_investment_percentile FLOAT;
    v_citywide_avg_sentiment FLOAT;
    v_citywide_avg_growth FLOAT;
    v_citywide_avg_investment FLOAT;
    v_total_locations INT;
    v_sentiment_label TEXT;
    v_growth_label TEXT;
    v_investment_label TEXT;
BEGIN
    -- Get INDIVIDUAL location data from location_insights
    SELECT 
        li.location_name,
        li.avg_sentiment_score,
        li.growth_score,
        li.investment_score
    INTO 
        v_location_name,
        v_sentiment_score,
        v_growth_score,
        v_investment_score
    FROM location_insights li
    WHERE li.location_id = loc_id;
    
    IF v_location_name IS NULL THEN
        RETURN;
    END IF;
    
    -- Calculate CITY-WIDE AVERAGES for benchmarking (all locations)
    SELECT 
        COALESCE(AVG(li.avg_sentiment_score), 0),
        COALESCE(AVG(li.growth_score), 0),
        COALESCE(AVG(li.investment_score), 0),
        COUNT(*)
    INTO 
        v_citywide_avg_sentiment,
        v_citywide_avg_growth,
        v_citywide_avg_investment,
        v_total_locations
    FROM location_insights li
    WHERE li.avg_sentiment_score IS NOT NULL;
    
    -- Calculate percentile ranks (percentage of locations with LOWER scores)
    -- Sentiment percentile
    SELECT ROUND((COUNT(*)::FLOAT / NULLIF(v_total_locations, 0) * 100)::NUMERIC, 0)
    INTO v_sentiment_percentile
    FROM location_insights li
    WHERE li.avg_sentiment_score < v_sentiment_score;
    
    -- Growth percentile
    SELECT ROUND((COUNT(*)::FLOAT / NULLIF(v_total_locations, 0) * 100)::NUMERIC, 0)
    INTO v_growth_percentile
    FROM location_insights li
    WHERE li.growth_score < v_growth_score;
    
    -- Investment percentile
    SELECT ROUND((COUNT(*)::FLOAT / NULLIF(v_total_locations, 0) * 100)::NUMERIC, 0)
    INTO v_investment_percentile
    FROM location_insights li
    WHERE li.investment_score < v_investment_score;
    
    -- Convert scores to 0-100 scale
    -- Sentiment: -1 to +1 range → 0 to 100 scale: (sentiment + 1) / 2 * 100
    v_sentiment_score := ROUND(((v_sentiment_score + 1) / 2 * 100)::NUMERIC, 0);
    v_citywide_avg_sentiment := ROUND(((v_citywide_avg_sentiment + 1) / 2 * 100)::NUMERIC, 0);
    
    -- Growth and Investment: 0-1 range → 0-100 scale
    v_growth_score := ROUND((v_growth_score * 100)::NUMERIC, 0);
    v_investment_score := ROUND((v_investment_score * 100)::NUMERIC, 0);
    v_citywide_avg_growth := ROUND((v_citywide_avg_growth * 100)::NUMERIC, 0);
    v_citywide_avg_investment := ROUND((v_citywide_avg_investment * 100)::NUMERIC, 0);
    
    -- Determine labels based on percentile
    v_sentiment_label := CASE 
        WHEN v_sentiment_percentile >= 80 THEN 'Highly Optimistic'
        WHEN v_sentiment_percentile >= 60 THEN 'Optimistic'
        WHEN v_sentiment_percentile >= 40 THEN 'Neutral'
        WHEN v_sentiment_percentile >= 20 THEN 'Cautious'
        ELSE 'Pessimistic'
    END;
    
    v_growth_label := CASE 
        WHEN v_growth_percentile >= 80 THEN 'Rapidly Developing'
        WHEN v_growth_percentile >= 60 THEN 'Developing'
        WHEN v_growth_percentile >= 40 THEN 'Steady'
        WHEN v_growth_percentile >= 20 THEN 'Slow Growth'
        ELSE 'Stagnant'
    END;
    
    v_investment_label := CASE 
        WHEN v_investment_percentile >= 80 THEN 'Premium'
        WHEN v_investment_percentile >= 60 THEN 'High Value'
        WHEN v_investment_percentile >= 40 THEN 'Moderate'
        WHEN v_investment_percentile >= 20 THEN 'Emerging'
        ELSE 'Budget'
    END;
    
    -- Return the results
    RETURN QUERY SELECT 
        loc_id,
        v_location_name,
        v_sentiment_score,
        v_growth_score,
        v_investment_score,
        COALESCE(v_sentiment_percentile, 0),
        COALESCE(v_growth_percentile, 0),
        COALESCE(v_investment_percentile, 0),
        v_citywide_avg_sentiment,
        v_citywide_avg_growth,
        v_citywide_avg_investment,
        v_total_locations,
        v_sentiment_label,
        v_growth_label,
        v_investment_label;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_location_intelligence_scores(INT) TO anon;
GRANT EXECUTE ON FUNCTION get_location_intelligence_scores(INT) TO authenticated;

-- =====================================================
-- USAGE:
-- SELECT * FROM get_location_intelligence_scores(1);
-- Expected for Gachibowli:
-- sentiment_score: 66 (from 0.32 converted)
-- growth_score: 94 (from 0.94 * 100)
-- investment_score: 91 (from 0.91 * 100)
-- =====================================================
