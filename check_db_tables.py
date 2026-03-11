"""
Check database tables and find location columns
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
print("DATABASE TABLES")
print("="*80)

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")

tables = cur.fetchall()
print(f"\nFound {len(tables)} tables:\n")
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*80)
print("LOCATION-RELATED COLUMNS")
print("="*80)

# Find location columns
cur.execute("""
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND (
        column_name ILIKE '%location%' OR
        column_name ILIKE '%village%' OR
        column_name ILIKE '%locality%' OR
        column_name ILIKE '%area%' OR
        column_name ILIKE '%mandal%' OR
        column_name ILIKE '%district%' OR
        column_name ILIKE '%place%'
    )
    ORDER BY table_name, column_name
""")

columns = cur.fetchall()
print(f"\nFound {len(columns)} location-related columns:\n")
for table, column, dtype in columns:
    print(f"  {table}.{column} ({dtype})")

# Check for specific tables that might have location data
print("\n" + "="*80)
print("CHECKING COMMON TABLES")
print("="*80)

common_tables = [
    'locations', 'hyderabad_locations', 'property_data', 
    'properties', 'real_estate_data', 'location_insights',
    'location_data', 'amenities'
]

for table_name in common_tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        print(f"\n✅ {table_name}: {count} records")
        
        # Get columns
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        cols = [c[0] for c in cur.fetchall()]
        print(f"   Columns: {', '.join(cols)}")
        
    except Exception as e:
        print(f"❌ {table_name}: {str(e).split('LINE')[0].strip()}")

cur.close()
conn.close()
