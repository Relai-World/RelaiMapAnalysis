import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_locations():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        # Get count of unique locations in corpus
        cur.execute("SELECT DISTINCT location_name FROM news_balanced_corpus")
        scraped_locations = sorted([row[0] for row in cur.fetchall()])
        
        # known non-hyd locations if any
        non_hyd = ["Bengaluru Urban"]
        hyd_locations = [loc for loc in scraped_locations if loc not in non_hyd]
        
        print(f"Total unique locations in DB: {len(scraped_locations)}")
        print(f"Hyderabad specific locations scraped: {len(hyd_locations)}")
        print(f"Non-Hyderabad locations found: {', '.join([loc for loc in scraped_locations if loc in non_hyd])}")
        
        # Check current batch status
        cur.execute("SELECT MAX(location_id) FROM news_balanced_corpus")
        max_id = cur.fetchone()[0]
        print(f"Max location ID scraped: {max_id}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_locations()
