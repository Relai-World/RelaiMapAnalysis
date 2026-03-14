import psycopg2
import math
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT"),
        sslmode='require'
    )

# ---------------- HELPERS ----------------
def clamp(value, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, value))

def compute_growth_score(avg_sentiment, article_count):
    """
    Activity-Driven Growth Logic (V2):
    1. Volume is the primary driver of 'Growth' (Construction = Dust = Complaints, but also = Growth).
    2. Sentiment acts as a slight modifier/bonus, not a gatekeeper.
    """
    if article_count == 0:
        return 0.0

    # 1. BUZZ SCORE (Logarithmic Scale)
    # 10 articles -> 1.0
    # 100 articles -> 2.0
    # 1000 articles -> 3.0 (Tier 1 Hub)
    buzz = math.log(article_count + 1, 10)
    
    # Normalize Buzz to 0-1 scale (Assuming max ~3000 articles => ~3.5)
    buzz_normalized = clamp(buzz / 3.5)

    # 2. SENTIMENT MODIFIER (Calibrated V3)
    # Map -0.5..0.5 to 0..1 (Matches Frontend Calibration)
    sentiment_normalized = clamp(avg_sentiment + 0.5)
    
    # 3. FINAL WEIGHTED SCORE
    # 80% Buzz (Activity), 20% Sentiment (Quality)
    final_score = (0.8 * buzz_normalized) + (0.2 * sentiment_normalized)
    
    # Boost factor for High Volume hubs to push them into the 0.8-0.9 range
    if article_count > 500:
        final_score *= 1.2

    return clamp(final_score)

def compute_investment_score(growth_score, avg_sentiment):
    """
    Investment Potential (V2):
    - Highly correlated with Growth (Booming area = Good Investment).
    - But heavily penalized by negative sentiment (Risk factor).
    """
    # Calibrated Sentiment Normalization (Matches Frontend)
    sentiment_normalized = clamp(avg_sentiment + 0.5)
    
    # Investment = 70% Growth Potenial + 30% "Vibe Check" (Sentiment)
    # If it's growing but everyone hates it, it's a risky investment.
    score = (0.7 * growth_score) + (0.3 * sentiment_normalized)
    
    return clamp(score)

# ---------------- MAIN AGGREGATION ----------------
def run():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all locations
    cur.execute("SELECT id FROM locations")
    locations = cur.fetchall()

    for (location_id,) in locations:

        # -------- SENTIMENT + ACTIVITY AGGREGATION --------
        # -------- SENTIMENT + ACTIVITY AGGREGATION (NEW SOURCE) --------
        cur.execute("""
            SELECT
                COUNT(id) AS article_count,
                AVG(sentiment_score) AS avg_sentiment,
                AVG(confidence) AS avg_confidence
            FROM news_balanced_corpus_1
            WHERE location_id = %s
              AND sentiment_score IS NOT NULL
        """, (location_id,))

        article_count, avg_sentiment, avg_confidence = cur.fetchone()

        article_count = article_count or 0
        avg_sentiment = float(avg_sentiment) if avg_sentiment is not None else 0.0
        avg_confidence = float(avg_confidence) if avg_confidence is not None else 0.0

        # -------- RE-CALCULATE SCORES --------
        growth_score = compute_growth_score(avg_sentiment, article_count)
        
        # Investment Score (V3 - Pure 70/30)
        investment_score = compute_investment_score(growth_score, avg_sentiment)

        # -------- UPSERT LOCATION INSIGHTS --------
        cur.execute("""
            INSERT INTO location_insights (
                location_id,
                avg_sentiment_score,
                growth_score,
                investment_score,
                last_updated
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (location_id)
            DO UPDATE SET
                avg_sentiment_score = EXCLUDED.avg_sentiment_score,
                growth_score = EXCLUDED.growth_score,
                investment_score = EXCLUDED.investment_score,
                last_updated = EXCLUDED.last_updated
        """, (
            location_id,
            avg_sentiment,
            growth_score,
            investment_score,
            datetime.now()
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("[OK] Location insights aggregation completed successfully.")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run()
