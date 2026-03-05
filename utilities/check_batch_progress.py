import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_progress():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        # Get count of articles for the latest IDs in the batch
        batch_ids = [
            221, 222, 223, 224, 225, 228, 229, 230, 231, 232, 233, 234, 236, 238, 239, 
            242, 243, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262
        ]
        
        print("Progress on current batch (ID: Name - Status):")
        for loc_id in batch_ids:
            cur.execute("SELECT location_name, COUNT(*) FROM news_balanced_corpus WHERE location_id = %s GROUP BY location_name", (loc_id,))
            res = cur.fetchone()
            if res:
                print(f"{loc_id}: {res[0]} - {res[1]} articles (Done)")
            else:
                print(f"{loc_id}: Pending...")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_progress()
