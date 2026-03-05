
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def check_counts():
    conn = psycopg2.connect(
        dbname="real_estate_intelligence",
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432
    )

    print("\n📊 DATA DISTRIBUTION CHECK")
    print("==========================")

    # 1. Raw Data Counts per Location
    print("\n🔹 RAW Scraped Data Count per Location:")
    df_raw = pd.read_sql_query("""
        SELECT l.name, l.id as loc_id, COUNT(r.id) as raw_count
        FROM locations l
        LEFT JOIN raw_scraped_data r ON l.id = r.location_id
        GROUP BY l.id, l.name
        ORDER BY l.id;
    """, conn)
    print(df_raw.to_string(index=False))

    # 2. Processed Sentiment Counts per Location
    print("\n🔹 PROCESSED Sentiment Data Count per Location (joined via raw):")
    df_sent = pd.read_sql_query("""
        SELECT l.name, l.id as loc_id, COUNT(p.id) as sentiment_count
        FROM locations l
        LEFT JOIN raw_scraped_data r ON l.id = r.location_id
        LEFT JOIN processed_sentiment_data p ON p.raw_data_id = r.id
        GROUP BY l.id, l.name
        ORDER BY l.id;
    """, conn)
    print(df_sent.to_string(index=False))

    conn.close()

if __name__ == "__main__":
    check_counts()
