
import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def analyze_db_content():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        cur = conn.cursor()

        print("\n🔍 ANALYZING CONTENT QUALITY")
        print("=" * 60)

        # Count total
        cur.execute("SELECT COUNT(*) FROM news_balanced_corpus")
        total = cur.fetchone()[0]
        print(f"Total Rows: {total}")

        # Check content length distribution
        cur.execute("""
            SELECT 
                PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY LENGTH(content)) as median_len,
                AVG(LENGTH(content)) as avg_len,
                MIN(LENGTH(content)) as min_len,
                MAX(LENGTH(content)) as max_len
            FROM news_balanced_corpus
        """)
        median, avg, min_l, max_l = cur.fetchone()
        
        print(f"\n📊 Length Stats (Chars):")
        print(f"   Median: {median:.0f}")
        print(f"   Average: {avg:.0f}")
        print(f"   Min: {min_l}")
        print(f"   Max: {max_l}")

        # Classify roughly
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE LENGTH(content) < 500) as short_summary,
                COUNT(*) FILTER (WHERE LENGTH(content) BETWEEN 500 AND 1500) as medium_article,
                COUNT(*) FILTER (WHERE LENGTH(content) > 1500) as long_article
            FROM news_balanced_corpus
        """)
        short, med, long = cur.fetchone()

        print(f"\n📉 Classification:")
        print(f"   Potential Summaries (<500 chars): {short} ({short/total*100:.1f}%)")
        print(f"   Short Articles (500-1500 chars): {med} ({med/total*100:.1f}%)")
        print(f"   Long Articles (>1500 chars): {long} ({long/total*100:.1f}%)")

        print("\n📝 Sample of Short Content (<300 chars):")
        cur.execute("SELECT url, content FROM news_balanced_corpus WHERE LENGTH(content) < 300 LIMIT 3")
        rows = cur.fetchall()
        for url, content in rows:
            snippet = content.replace('\n', ' ')[:100]
            print(f"   🔗 {url[:60]}... -> {snippet}...")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_db_content()
