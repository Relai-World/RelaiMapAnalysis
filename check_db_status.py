
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        # Check tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [t[0] for t in cur.fetchall()]
        print(f"Tables found: {tables}")
        
        # Check Gachibowli
        cur.execute("SELECT id, name FROM locations WHERE name = 'Gachibowli'")
        loc = cur.fetchone()
        print(f"Location Gachibowli: {loc}")
        
        if loc:
            cur.execute("SELECT * FROM location_insights WHERE location_id = %s", (loc[0],))
            insight = cur.fetchone()
            print(f"Insight for Gachibowli: {insight}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
