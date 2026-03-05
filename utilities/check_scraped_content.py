
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    host=os.getenv("DB_HOST", "localhost"),
    port=5432
)
cur = conn.cursor()

# Fetch latest 10 records
cur.execute("""
    SELECT location_name, url, content 
    FROM news_balanced_corpus 
    ORDER BY id DESC 
    LIMIT 10
""")

print(f"{'Location':<20} | {'Relevance Check (Snippet)'}")
print("-" * 80)

for loc, url, content in cur.fetchall():
    # Check if location name is in content (simple check)
    is_relevant = loc.lower() in content.lower()
    snippet = content[:100].replace('\n', ' ')
    relevance_mark = "✅" if is_relevant else "⚠️"
    print(f"{loc:<20} | {relevance_mark} {snippet}...")

conn.close()
