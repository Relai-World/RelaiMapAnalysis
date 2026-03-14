import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    port=os.getenv('DB_PORT'),
    sslmode='require'
)

cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'location_insights' 
    ORDER BY ordinal_position
""")

print("location_insights table schema:")
print("-" * 50)
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n\nSample data:")
print("-" * 50)
cur.execute("SELECT * FROM location_insights LIMIT 1")
sample = cur.fetchone()
if sample:
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'location_insights' 
        ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    for i, col in enumerate(cols):
        print(f"{col}: {sample[i]}")

cur.close()
conn.close()
