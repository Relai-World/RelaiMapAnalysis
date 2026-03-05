
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_schema():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432
    )
    cur = conn.cursor()

    print("🔨 Updating 'news_balanced_corpus' schema for Option A...")

    # 1. Add Sentiment Columns
    try:
        cur.execute("ALTER TABLE news_balanced_corpus ADD COLUMN sentiment_score FLOAT;")
    except psycopg2.errors.DuplicateColumn:
        conn.rollback()
        print("   - sentiment_score already exists.")
    else:
        conn.commit()
        print("   - Added sentiment_score column.")

    try:
        cur.execute("ALTER TABLE news_balanced_corpus ADD COLUMN sentiment_label VARCHAR(20);")
    except psycopg2.errors.DuplicateColumn:
        conn.rollback()
        print("   - sentiment_label already exists.")
    else:
        conn.commit()
        print("   - Added sentiment_label column.")
        
    try:
        cur.execute("ALTER TABLE news_balanced_corpus ADD COLUMN confidence FLOAT;")
    except psycopg2.errors.DuplicateColumn:
        conn.rollback()
        print("   - confidence already exists.")
    else:
        conn.commit()
        print("   - Added confidence column.")

    conn.close()
    print("✅ Migration Complete.")

if __name__ == "__main__":
    migrate_schema()
