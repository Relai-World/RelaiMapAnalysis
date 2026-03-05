
import psycopg2
import os
import sys
# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

load_dotenv()

def view_data():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()

    print("\n🔍 VIEWING UNBIASED DATA (Top 20 most recent)\n")
    print(f"{'Location':<20} | {'Source':<20} | {'Content Snippet (First 100 chars)'}")
    print("-" * 100)

    cur.execute("""
        SELECT location_name, source, content 
        FROM news_balanced_corpus 
        ORDER BY id DESC 
        LIMIT 20
    """)
    
    rows = cur.fetchall()
    
    if not rows:
        print("📭 No data found yet.")
    
    for row in rows:
        loc, src, content = row
        snippet = content[:100].replace('\n', ' ') if content else "(No Content)"
        print(f"{loc:<20} | {src:<20} | {snippet}...")

    conn.close()

if __name__ == "__main__":
    view_data()
