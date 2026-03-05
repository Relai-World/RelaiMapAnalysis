
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_table():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()

    print("🔨 Creating new table: news_balanced_corpus...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news_balanced_corpus (
            id SERIAL PRIMARY KEY,
            location_name VARCHAR(255),
            source VARCHAR(255),
            url TEXT UNIQUE,
            content TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Optional: Clear it if you want strict fresh start (user asked for new table, usually implies empty)
    # But "create a new table" could mean just structure. 
    # Let's clear it to be safe and ensure "equal importance" from scratch.
    cur.execute("TRUNCATE TABLE news_balanced_corpus;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Table created and ready for unbiased data.")

if __name__ == "__main__":
    create_table()
