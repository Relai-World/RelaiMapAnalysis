
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def list_tables_in_target_db():
    print(f"\n📂 DATABASE: real_estate_intelligence")
    print("====================================")
    try:
        conn = psycopg2.connect(
            dbname="real_estate_intelligence",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        cur = conn.cursor()
        
        # Get count and names of all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        rows = cur.fetchall()
        
        if not rows:
            print("❌ No tables found.")
        else:
            print(f"✅ Found {len(rows)} Tables:\n")
            for r in rows:
                tname = r[0]
                # Get row count for each
                cur.execute(f"SELECT COUNT(*) FROM {tname}")
                count = cur.fetchone()[0]
                print(f"  🔹 {tname:<30} (Rows: {count})")
            
        print("\n====================================")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_tables_in_target_db()
