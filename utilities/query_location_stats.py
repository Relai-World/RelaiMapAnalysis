import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode='require' if os.getenv("DB_HOST", "localhost") != 'localhost' else 'prefer'
    )

print("=" * 100)
print("QUERYING DATABASE FOR LOCATION STATISTICS")
print("=" * 100)
print()

conn = get_db()
cur = conn.cursor()

# Location patterns
locations = {
    'Financial District': "areaname ILIKE '%Financial District%' OR projectlocation ILIKE '%Financial District%' OR google_place_address ILIKE '%Financial District%'",
    'Gachibowli': "areaname ILIKE '%Gachibowli%' OR projectlocation ILIKE '%Gachibowli%' OR google_place_address ILIKE '%Gachibowli%'",
    'HITEC City': "(areaname ILIKE '%HITEC%' OR areaname ILIKE '%Hitech%' OR areaname ILIKE '%Hi-Tech%' OR projectlocation ILIKE '%HITEC%' OR projectlocation ILIKE '%Hitech%' OR google_place_address ILIKE '%HITEC%' OR google_place_address ILIKE '%Hitech%')",
    'Kondapur': "areaname ILIKE '%Kondapur%' OR projectlocation ILIKE '%Kondapur%' OR google_place_address ILIKE '%Kondapur%'",
    'Kukatpally': "(areaname ILIKE '%Kukatpally%' OR areaname ILIKE '%KPHB%' OR projectlocation ILIKE '%Kukatpally%' OR google_place_address ILIKE '%Kukatpally%')",
    'Madhapur': "areaname ILIKE '%Madhapur%' OR projectlocation ILIKE '%Madhapur%' OR google_place_address ILIKE '%Madhapur%'",
    'Nanakramguda': "areaname ILIKE '%Nanakramguda%' OR projectlocation ILIKE '%Nanakramguda%' OR google_place_address ILIKE '%Nanakramguda%'"
}

total_properties = 0

for location, where_clause in locations.items():
    query = f"""
        SELECT 
            COUNT(*) as count,
            ROUND(AVG(baseprojectprice), 2) as avg_base_price,
            ROUND(AVG(price_per_sft), 2) as avg_price_sqft,
            MIN(baseprojectprice) as min_base,
            MAX(baseprojectprice) as max_base,
            MIN(price_per_sft) as min_sqft,
            MAX(price_per_sft) as max_sqft
        FROM csv_properties
        WHERE {where_clause}
    """
    
    cur.execute(query)
    row = cur.fetchone()
    
    count = row[0]
    total_properties += count
    
    print(f"📍 {location.upper()}")
    print(f"   {'─' * 80}")
    print(f"   Properties Found:       {count:,}")
    
    if count > 0 and row[1]:
        print(f"   Avg Base Price:         ₹{row[1]/10000000:.2f} Cr")
        print(f"   Avg Price/SqFt:         ₹{row[2]:,.0f}")
        print(f"   Base Price Range:       ₹{row[3]/10000000:.2f} Cr - ₹{row[4]/10000000:.2f} Cr")
        print(f"   Price/SqFt Range:       ₹{row[5]:,.0f} - ₹{row[6]:,.0f}")
    else:
        print(f"   No pricing data available")
    
    print()

print("=" * 100)
print(f"📊 TOTAL PROPERTIES ANALYZED: {total_properties:,}")
print("=" * 100)

cur.close()
conn.close()
