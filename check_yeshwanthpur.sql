-- Check Yeshwanthpur data in location_insights table
SELECT 
    l.id,
    l.name,
    li.avg_sentiment_score,
    li.growth_score,
    li.investment_score,
    li.sentiment_summary,
    li.growth_summary,
    li.invest_summary
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id
WHERE l.name ILIKE '%Yeshwanthpur%';

-- Check what get_all_insights returns for Yeshwanthpur
SELECT 
    location_id,
    location,
    avg_sentiment,
    growth_score,
    investment_score,
    sentiment_summary,
    growth_summary,
    invest_summary
FROM get_all_insights()
WHERE location ILIKE '%Yeshwanthpur%';
