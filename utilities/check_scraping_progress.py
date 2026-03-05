
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

# Count records where ID > 2417 (baseline from step 1173)
cur.execute("""
    SELECT COUNT(*), location_name 
    FROM news_balanced_corpus 
    WHERE id > 2417
    GROUP BY location_name
    ORDER BY COUNT(*) DESC
""")

rows = cur.fetchall()
total = sum(r[0] for r in rows)

print(f"Total New Records (ID > 2417): {total}")
print("-" * 40)
print(f"{'Location':<30} | {'Count'}")
print("-" * 40)
for loc, count in rows:
    print(f"{loc:<30} | {count}")

cur.close()
conn.close()
