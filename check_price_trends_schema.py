import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432")
)
cursor = conn.cursor()

# Get table schema
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'price_trends'
    ORDER BY ordinal_position
""")

print("price_trends table schema:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.close()
conn.close()
