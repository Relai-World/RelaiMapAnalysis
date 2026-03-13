
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def list_locations():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        cur.execute("SELECT id, name FROM locations")
        rows = cur.fetchall()
        print(f"Total Locations: {len(rows)}")
        for r in rows:
            print(f"- {r[1]} (id: {r[0]})")
            
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [t[0] for t in cur.fetchall()]
        print(f"Tables: {tables}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_locations()
