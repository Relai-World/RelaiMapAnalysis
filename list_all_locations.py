"""
List All Hyderabad Locations
Simple script to display all locations from database
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

print("\n" + "="*80)
print("📍 ALL HYDERABAD LOCATIONS")
print("="*80)

query = """
    SELECT id, name
    FROM locations
    WHERE city = 'Hyderabad'
    ORDER BY name
"""

cur.execute(query)
locations = cur.fetchall()

print(f"\nTotal: {len(locations)} locations\n")

for idx, (location_id, name) in enumerate(locations, 1):
    print(f"{idx:3d}. {name}")

print("\n" + "="*80)

cur.close()
conn.close()
