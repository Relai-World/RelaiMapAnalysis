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
    WHERE table_name = 'registration_transactions' 
    ORDER BY ordinal_position
""")

print("registration_transactions table structure:")
print("=" * 60)
for col, dtype in cur.fetchall():
    print(f"{col}: {dtype}")

# Get sample data
print("\n\nSample data (first 3 rows):")
print("=" * 60)
cur.execute("SELECT * FROM registration_transactions LIMIT 3")
rows = cur.fetchall()
for row in rows:
    print(row)

# Check locations table
print("\n\nLocations table sample:")
print("=" * 60)
cur.execute("SELECT id, name FROM locations WHERE id IN (37, 66, 177, 209, 214) ORDER BY id")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}")

cur.close()
conn.close()
