import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST")
)

cur = conn.cursor()

# Get table schema
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'location_costs' 
    ORDER BY ordinal_position
""")

print("\n📋 location_costs TABLE SCHEMA:")
print("=" * 60)
for row in cur.fetchall():
    print(f"{row[0]:30s} {row[1]}")

print("=" * 60)

cur.close()
conn.close()
