import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def list_all_scraped_locations():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        # Get unique locations and their article counts
        cur.execute("""
            SELECT location_id, location_name, COUNT(*) 
            FROM news_balanced_corpus 
            GROUP BY location_id, location_name 
            ORDER BY location_id
        """)
        rows = cur.fetchall()
        
        print(f"Total unique locations in DB: {len(rows)}")
        print("\nBreakdown (ID: Name - Count):")
        for row in rows:
            print(f"{row[0]}: {row[1]} - {row[2]} articles")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_scraped_locations()
