"""
Find ALL locations and their exact record counts
Including locations with 0 records
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
print("ALL HYDERABAD LOCATIONS WITH RECORD COUNTS")
print("="*80)

# Get all Hyderabad locations
cur.execute("""
    SELECT id, name
    FROM locations
    WHERE city = 'Hyderabad'
    ORDER BY id
""")

all_locations = cur.fetchall()
print(f"\nTotal Hyderabad locations: {len(all_locations)}\n")

# For each location, count records across all tables
location_data = []

for loc_id, loc_name in all_locations:
    total_count = 0
    
    # Count in location_infrastructure
    cur.execute("SELECT COUNT(*) FROM location_infrastructure WHERE location_id = %s", (loc_id,))
    total_count += cur.fetchone()[0]
    
    # Count in location_costs
    cur.execute("SELECT COUNT(*) FROM location_costs WHERE location_id = %s", (loc_id,))
    total_count += cur.fetchone()[0]
    
    # Count in location_insights
    cur.execute("SELECT COUNT(*) FROM location_insights WHERE location_id = %s", (loc_id,))
    total_count += cur.fetchone()[0]
    
    # Count in price_trends
    cur.execute("SELECT COUNT(*) FROM price_trends WHERE location_id = %s", (loc_id,))
    total_count += cur.fetchone()[0]
    
    # Count in news_balanced_corpus
    cur.execute("SELECT COUNT(*) FROM news_balanced_corpus WHERE location_id = %s", (loc_id,))
    total_count += cur.fetchone()[0]
    
    # Count in raw_scraped_data
    cur.execute("SELECT COUNT(*) FROM raw_scraped_data WHERE location_id = %s", (loc_id,))
    total_count += cur.fetchone()[0]
    
    location_data.append((loc_id, loc_name, total_count))

# Sort by count
location_data.sort(key=lambda x: x[2])

print("="*80)
print("LOCATIONS WITH LESS THAN 70 RECORDS")
print("="*80)

low_count = [(loc_id, name, count) for loc_id, name, count in location_data if count < 70]

print(f"\nFound {len(low_count)} locations with < 70 records:\n")

for loc_id, name, count in low_count:
    print(f"({loc_id}, '{name}') - {count} records")

# Show zero record locations
print("\n" + "="*80)
print("LOCATIONS WITH 0 RECORDS")
print("="*80)

zero_count = [(loc_id, name) for loc_id, name, count in location_data if count == 0]

if zero_count:
    print(f"\nFound {len(zero_count)} locations with 0 records:\n")
    for loc_id, name in zero_count:
        print(f"({loc_id}, '{name}')")
else:
    print("\n✅ No locations with 0 records!")

print("\n" + "="*80)

cur.close()
conn.close()
