
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
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='area_boundaries'")
print("Columns in area_boundaries:")
for row in cur.fetchall():
    print(row[0])

cur.execute("SELECT * FROM area_boundaries LIMIT 1")
print("\nSample Data:")
print(cur.fetchone())

conn.close()
