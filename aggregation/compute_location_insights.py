import psycopg2
import math

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        dbname="real_estate_intelligence",
        user="postgres",
        password="post@123",
        host="localhost",
        port=5432
    )

# ---------------- SCORE HELPERS ----------------
def clamp(value, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, value))

def compute_growth_score(avg_sentiment, article_count):
    """
    Simple, explainable growth signal.
    """
    volume_factor = math.log(article_count + 1, 10)
    score = avg_sentiment * volume_factor
    return clamp((score + 1) / 2)

def compute_investment_score(growth_score, confidence):
    """
    Conservative investment signal.
    """
    return clamp(0.7 * growth_score + 0.3 * confidence)

# ---------------- MAIN AGGREGATION ----------------
def run():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all locations
    cur.execute("SELECT id FROM locations")
    locations = cur.fetchall()

    for (location_id,) in locations:

        cur.execute("""
            SELECT
                COUNT(p.id) AS article_count,
                AVG(p.sentiment_score) AS avg_sentiment,
                AVG(p.confidence) AS avg_confidence
            FROM processed_sentiment_data p
            JOIN raw_scraped_data r
                ON p.raw_data_id = r.id
            WHERE r.location_id = %s
        """, (location_id,))

        article_count, avg_sentiment, avg_confidence = cur.fetchone()

        # Normalize DB numeric types
        article_count = article_count or 0
        avg_sentiment = float(avg_sentiment) if avg_sentiment is not None else 0.0
        avg_confidence = float(avg_confidence) if avg_confidence is not None else 0.0

        growth_score = compute_growth_score(avg_sentiment, article_count)
        investment_score = compute_investment_score(growth_score, avg_confidence)

        # Upsert WITHOUT updated_at
        cur.execute("""
            INSERT INTO location_insights
                (location_id,
                 avg_sentiment_score,
                 growth_score,
                 investment_score)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (location_id)
            DO UPDATE SET
                avg_sentiment_score = EXCLUDED.avg_sentiment_score,
                growth_score = EXCLUDED.growth_score,
                investment_score = EXCLUDED.investment_score
        """, (
            location_id,
            avg_sentiment,
            growth_score,
            investment_score
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Location insights aggregation completed successfully.")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run()
