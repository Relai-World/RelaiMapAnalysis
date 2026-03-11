"""
Find locations with less than 70 records
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
print("LOCATIONS WITH LESS THAN 70 RECORDS")
print("="*80)

# Get all Hyderabad locations first
cur.execute("""
    SELECT id, name
    FROM locations
    WHERE city = 'Hyderabad'
    ORDER BY name
""")

all_locations = cur.fetchall()
print(f"\nTotal Hyderabad locations: {len(all_locations)}\n")

# Initialize counts for all locations
location_counts = {name: {'id': loc_id, 'total': 0} for loc_id, name in all_locations}

# Find tables that reference location_id
print("Checking all tables with location references...\n")

# Check each table that might have location data
tables_to_check = [
    'location_infrastructure',
    'location_costs',
    'location_insights',
    'price_trends',
    'news_balanced_corpus',
    'raw_scraped_data',
    'listings',
    'registration_transactions'
]

for table in tables_to_check:
    try:
        # Check if table has location_id column
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            AND column_name IN ('location_id', 'locality')
        """)
        
        col_result = cur.fetchone()
        if not col_result:
            continue
        
        col_name = col_result[0]
        
        # Get counts
        if col_name == 'location_id':
            cur.execute(f"""
                SELECT l.id, l.name, COUNT(t.*) as count
                FROM locations l
                LEFT JOIN {table} t ON l.id = t.location_id
                WHERE l.city = 'Hyderabad'
                GROUP BY l.id, l.name
            """)
        else:
            cur.execute(f"""
                SELECT l.id, l.name, COUNT(t.*) as count
                FROM locations l
                LEFT JOIN {table} t ON l.name = t.locality
                WHERE l.city = 'Hyderabad'
                GROUP BY l.id, l.name
            """)
        
        results = cur.fetchall()
        
        for loc_id, loc_name, count in results:
            if loc_name in location_counts:
                location_counts[loc_name]['total'] += count
        
        print(f"✅ Checked {table}: found data for locations")
        
    except Exception as e:
        print(f"⚠️  Skipped {table}: {e}")

print("\n" + "="*80)
print("RESULTS")
print("="*80)

# Filter locations with less than 70 records
low_count_locations = [
    (data['id'], name, data['total']) 
    for name, data in location_counts.items() 
    if data['total'] < 70
]

# Sort by count
low_count_locations.sort(key=lambda x: x[2])

print(f"\nFound {len(low_count_locations)} locations with less than 70 records:\n")

for loc_id, name, count in low_count_locations:
    print(f"({loc_id}, '{name}') - {count} records")

print("\n" + "="*80)
print(f"Total locations with < 70 records: {len(low_count_locations)}")
print("="*80)

# Also show locations with 0 records
zero_count = [(loc_id, name) for loc_id, name, count in low_count_locations if count == 0]
if zero_count:
    print(f"\n⚠️  Locations with 0 records: {len(zero_count)}")
    for loc_id, name in zero_count:
        print(f"   ({loc_id}, '{name}')")

cur.close()
conn.close()
