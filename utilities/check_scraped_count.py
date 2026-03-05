import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def count_scraped_locations():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        # Query to get unique location count
        cur.execute("SELECT COUNT(DISTINCT location_id) FROM news_balanced_corpus")
        count = cur.fetchone()[0]
        
        # Also get the names of some locations to be sure
        cur.execute("SELECT DISTINCT location_name FROM news_balanced_corpus ORDER BY location_name")
        locations = [row[0] for row in cur.fetchall()]
        
        print(f"Total unique locations scraped: {count}")
        print(f"Locations: {', '.join(locations[:10])} ... (and {max(0, count-10)} more)")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    count_scraped_locations()
