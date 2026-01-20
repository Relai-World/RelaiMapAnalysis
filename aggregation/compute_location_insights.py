import psycopg2
import math
from datetime import datetime

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        dbname="real_estate_intelligence",
        user="postgres",
        password="post@123",
        host="localhost",
        port=5432
    )

# ---------------- HELPERS ----------------
def clamp(value, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, value))

def compute_growth_score(avg_sentiment, article_count):
    """
    Robust growth signal calibrated for real-world news data.
    - News is naturally negative-biased
    - Activity volume must still matter
    """
    if article_count == 0:
        return 0.0

    volume_factor = math.log(article_count + 1, 10)

    # Neutralize news negativity bias
    adjusted_sentiment = avg_sentiment + 0.5

    raw_score = adjusted_sentiment * volume_factor

    # Normalize safely into 0–1
    return clamp(raw_score / 3.0)

def compute_investment_score(growth_score, confidence):
    """
    Conservative investment signal.
    Growth dominates, confidence stabilizes.
    """
    return clamp(
        0.7 * growth_score +
        0.3 * confidence
    )

# ---------------- MAIN AGGREGATION ----------------
def run():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all locations
    cur.execute("SELECT id FROM locations")
    locations = cur.fetchall()

    for (location_id,) in locations:

        # -------- SENTIMENT + ACTIVITY AGGREGATION --------
        cur.execute("""
            SELECT
                COUNT(r.id) AS article_count,
                AVG(p.sentiment_score) AS avg_sentiment,
                AVG(p.confidence) AS avg_confidence
            FROM raw_scraped_data r
            LEFT JOIN processed_sentiment_data p
                ON p.raw_data_id = r.id
            WHERE r.location_id = %s
        """, (location_id,))

        article_count, avg_sentiment, avg_confidence = cur.fetchone()

        article_count = article_count or 0
        avg_sentiment = float(avg_sentiment) if avg_sentiment is not None else 0.0
        avg_confidence = float(avg_confidence) if avg_confidence is not None else 0.0

        growth_score = compute_growth_score(avg_sentiment, article_count)
        investment_score = compute_investment_score(growth_score, avg_confidence)

        # -------- INFRA COUNTS (already in schema) --------
        cur.execute("""
            SELECT
                school_count,
                hospital_count
            FROM locations
            WHERE id = %s
        """, (location_id,))

        school_count, hospital_count = cur.fetchone()

        # -------- UPSERT LOCATION INSIGHTS --------
        cur.execute("""
            INSERT INTO location_insights (
                location_id,
                avg_sentiment_score,
                growth_score,
                investment_score,
                schools_count,
                hospitals_count,
                last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (location_id)
            DO UPDATE SET
                avg_sentiment_score = EXCLUDED.avg_sentiment_score,
                growth_score = EXCLUDED.growth_score,
                investment_score = EXCLUDED.investment_score,
                schools_count = EXCLUDED.schools_count,
                hospitals_count = EXCLUDED.hospitals_count,
                last_updated = EXCLUDED.last_updated
        """, (
            location_id,
            avg_sentiment,
            growth_score,
            investment_score,
            school_count,
            hospital_count,
            datetime.now()
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Location insights aggregation completed successfully.")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run()
