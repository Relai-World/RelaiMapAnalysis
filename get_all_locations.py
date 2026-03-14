import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Try with pooler connection (port 6543) for Supabase
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port="6543"  # Supabase pooler port
)

cur = conn.cursor()

# Get all locations
cur.execute("SELECT id, name FROM locations ORDER BY id")
locations = cur.fetchall()

print(f"Total locations found: {len(locations)}\n")
print("="*70)

# Format for Python list
print("\nPython list format:")
print("HYDERABAD_LOCATIONS = [")
for i, (loc_id, name) in enumerate(locations):
    if i < len(locations) - 1:
        print(f'    ({loc_id}, "{name}"),')
    else:
        print(f'    ({loc_id}, "{name}")')
print("]")

print("\n" + "="*70)
print(f"\nTotal: {len(locations)} locations")

cur.close()
conn.close()
