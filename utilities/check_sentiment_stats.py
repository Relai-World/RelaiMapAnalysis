
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_sentiment_values():
    conn = psycopg2.connect(
        dbname="real_estate_intelligence",
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432
    )
    cur = conn.cursor()

    print("\n🧐 DETAILED SENTIMENT CHECK (Kondapur ID=2)")
    print("==========================================")
    
    # Check if we can join
    cur.execute("""
        SELECT COUNT(*), AVG(p.sentiment_score), MIN(p.sentiment_score), MAX(p.sentiment_score)
        FROM raw_scraped_data r
        JOIN processed_sentiment_data p ON p.raw_data_id = r.id
        WHERE r.location_id = 2
    """)
    row = cur.fetchone()
    print(f"Count: {row[0]}")
    print(f"AVG:   {row[1]}")
    print(f"MIN:   {row[2]}")
    print(f"MAX:   {row[3]}")

    print("\n🧐 SAMPLE Invalid Scores?")
    cur.execute("""
        SELECT p.sentiment_score 
        FROM raw_scraped_data r
        JOIN processed_sentiment_data p ON p.raw_data_id = r.id
        WHERE r.location_id = 2
        LIMIT 10
    """)
    samples = cur.fetchall()
    print("First 10 scores:", [s[0] for s in samples])

    conn.close()

if __name__ == "__main__":
    check_sentiment_values()
