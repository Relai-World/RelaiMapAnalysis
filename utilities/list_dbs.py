
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def list_databases():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cur.fetchall()
        
        dbs = [r[0] for r in rows]
        
        for db in dbs:
            print(f"\n🔎 Checking database: {db}")
            try:
                conn_db = psycopg2.connect(
                    dbname=db,
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "post@123"),
                    host=os.getenv("DB_HOST", "localhost"),
                    port=5432
                )
                cur_db = conn_db.cursor()
                cur_db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
                tables = cur_db.fetchall()
                table_names = [t[0] for t in tables]
                
                if "intelligence_master_v2" in table_names:
                    print(f"   ✅ FOUND 'intelligence_master_v2' HERE! ({len(table_names)} tables total)")
                elif "raw_scraped_data" in table_names:
                    print(f"   ⚠️ Found 'raw_scraped_data' but NOT 'intelligence_master_v2'")
                else:
                    print(f"   ❌ Table not found. (Tables: {len(table_names)})")
                
                conn_db.close()
            except Exception as e:
                print(f"   ⚠️ Could not connect: {e}")

        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_databases()
