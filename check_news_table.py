import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

# Get table structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'news_balanced_corpus' 
    ORDER BY ordinal_position
""")

print("news_balanced_corpus table structure:")
print("=" * 60)
for col, dtype in cur.fetchall():
    print(f"{col}: {dtype}")

# Get sample data
print("\n\nSample data (first 2 rows):")
print("=" * 60)
cur.execute("SELECT * FROM news_balanced_corpus LIMIT 2")
colnames = [desc[0] for desc in cur.description]
print(f"Columns: {colnames}")
rows = cur.fetchall()
for row in rows:
    print("\n")
    for i, val in enumerate(row):
        print(f"  {colnames[i]}: {val}")

# Check which locations have data
print("\n\nLocations with news data:")
print("=" * 60)
cur.execute("""
    SELECT location_id, location_name, COUNT(*) as article_count
    FROM news_balanced_corpus
    GROUP BY location_id, location_name
    ORDER BY article_count DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Articles: {row[2]}")

cur.close()
conn.close()
