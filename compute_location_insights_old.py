import psycopg2
import numpy as np
from datetime import datetime

# -----------------------
# Database Connection
# -----------------------
conn = psycopg2.connect(
    dbname="real_estate_intelligence",
    user="postgres",
    password="post@123",
    host="localhost",
    port=5432
)
cur = conn.cursor()

# -----------------------
# Fetch all locations
# -----------------------
cur.execute("SELECT id FROM locations;")
locations = cur.fetchall()

for (location_id,) in locations:

    # -----------------------
    # Sentiment Aggregation
    # -----------------------
    cur.execute("""
        SELECT ps.sentiment_score
        FROM processed_sentiment_data ps
        JOIN raw_scraped_data rs
          ON ps.raw_data_id = rs.id
        WHERE rs.location_id = %s
    """, (location_id,))
    
    sentiments = [row[0] for row in cur.fetchall() if row[0] is not None]
    avg_sentiment = float(np.mean(sentiments)) if sentiments else 0.0
    sentiment_score_norm = (avg_sentiment + 1) * 50  # -1..1 → 0..100

    # -----------------------
    # Price Aggregation
    # -----------------------
    cur.execute("""
        SELECT price
        FROM raw_scraped_data
        WHERE location_id = %s AND price IS NOT NULL
    """, (location_id,))
    
    prices = [row[0] for row in cur.fetchall()]
    avg_price = float(np.mean(prices)) if prices else None

    if avg_price:
        price_trend = "increasing"
        price_trend_score = 70
    else:
        price_trend = "stable"
        price_trend_score = 40

    # -----------------------
    # Activity Score
    # -----------------------
    cur.execute("""
        SELECT COUNT(*)
        FROM raw_scraped_data
        WHERE location_id = %s
    """, (location_id,))
    
    activity_count = cur.fetchone()[0]
    activity_score = min(activity_count * 10, 100)

    # -----------------------
    # Growth Score
    # -----------------------
    growth_score = (
        0.4 * sentiment_score_norm +
        0.4 * price_trend_score +
        0.2 * activity_score
    )

    # -----------------------
    # Investment Score
    # -----------------------
    affordability_score = 60 if avg_price and avg_price < 10000000 else 40
    sentiment_stability = 60
    infra_signal_score = 50

    investment_score = (
        0.3 * growth_score +
        0.3 * affordability_score +
        0.2 * sentiment_stability +
        0.2 * infra_signal_score
    )

    # -----------------------
    # Upsert into location_insights
    # -----------------------
    cur.execute("""
        INSERT INTO location_insights (
            location_id,
            avg_sentiment_score,
            avg_price,
            price_trend,
            growth_score,
            investment_score,
            last_updated
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (location_id)
        DO UPDATE SET
            avg_sentiment_score = EXCLUDED.avg_sentiment_score,
            avg_price = EXCLUDED.avg_price,
            price_trend = EXCLUDED.price_trend,
            growth_score = EXCLUDED.growth_score,
            investment_score = EXCLUDED.investment_score,
            last_updated = EXCLUDED.last_updated;
    """, (
        location_id,
        avg_sentiment,
        avg_price,
        price_trend,
        growth_score,
        investment_score,
        datetime.now()
    ))

conn.commit()
cur.close()
conn.close()

print("Location insights computed successfully.")
