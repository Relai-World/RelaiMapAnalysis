import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432"),
    sslmode='require' if os.getenv("DB_HOST", "localhost") != 'localhost' else 'prefer'
)
cur = conn.cursor()
cur.execute("SELECT count(*), count(distinct location_name) FROM news_balanced_corpus_1 WHERE location_name ILIKE 'B%'")
print("Total rows starting with B, distinct locations starting with B:", cur.fetchone())

cur.execute("""
    SELECT location_name, location_id 
    FROM news_balanced_corpus_1 
    WHERE location_name ILIKE 'B%' 
    ORDER BY location_name 
    LIMIT 10
""")
print("Top 10 rows from db query:")
for row in cur.fetchall():
    print(row)
