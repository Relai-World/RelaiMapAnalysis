import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'post@123'),
    dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
    port=os.getenv('DB_PORT', '5432'),
    sslmode='require' if os.getenv('DB_HOST', 'localhost') != 'localhost' else 'prefer'
)

cur = conn.cursor()

print("=" * 100)
print("CSV_PROPERTIES TABLE - SAMPLE DATA")
print("=" * 100)
print()

# Get total count
cur.execute("SELECT COUNT(*) FROM csv_properties;")
total = cur.fetchone()[0]
print(f"Total records in csv_properties: {total:,}")
print()

# Show sample data from each location
locations = ['Gachibowli', 'Kondapur', 'Madhapur', 'HITEC', 'Kukatpally', 'Financial District', 'Nanakramguda']

for location in locations:
    print(f"📍 Sample {location} properties:")
    cur.execute(f"""
        SELECT projectname, areaname, price_per_sft, baseprojectprice
        FROM csv_properties
        WHERE areaname ILIKE '%{location}%' 
           OR projectlocation ILIKE '%{location}%'
           OR google_place_address ILIKE '%{location}%'
        LIMIT 3;
    """)
    
    rows = cur.fetchall()
    if rows:
        for i, row in enumerate(rows, 1):
            project = row[0] if row[0] else 'N/A'
            area = row[1] if row[1] else 'N/A'
            price_sqft = row[2] if row[2] else 0
            base_price = row[3] if row[3] else 0
            print(f"   {i}. {project[:40]:40s} | {area[:20]:20s} | ₹{price_sqft:,.0f}/sqft")
    else:
        print(f"   No data found")
    print()

print("=" * 100)
print("To query this table yourself, use:")
print("  SELECT * FROM csv_properties WHERE areaname ILIKE '%Gachibowli%';")
print("=" * 100)

cur.close()
conn.close()
