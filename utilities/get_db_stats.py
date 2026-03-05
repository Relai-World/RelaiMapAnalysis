import psycopg2
import pandas as pd
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
print("DATABASE QUERY RESULTS - ACCURATE COUNTS")
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

results = []

for location, where_clause in locations.items():
    query = f"""
        SELECT 
            COUNT(*) as count,
            AVG(baseprojectprice) as avg_base_price,
            AVG(price_per_sft) as avg_price_sqft,
            MIN(baseprojectprice) as min_base,
            MAX(baseprojectprice) as max_base,
            MIN(price_per_sft) as min_sqft,
            MAX(price_per_sft) as max_sqft
        FROM csv_properties
        WHERE {where_clause}
    """
    
    cur.execute(query)
    row = cur.fetchone()
    
    results.append({
        'Location': location,
        'Count': row[0],
        'Avg_Base_Price_Cr': round(row[1]/10000000, 2) if row[1] else 0,
        'Avg_Price_SqFt': round(row[2], 0) if row[2] else 0,
        'Min_Base_Cr': round(row[3]/10000000, 2) if row[3] else 0,
        'Max_Base_Cr': round(row[4]/10000000, 2) if row[4] else 0,
        'Min_Price_SqFt': round(row[5], 0) if row[5] else 0,
        'Max_Price_SqFt': round(row[6], 0) if row[6] else 0
    })
    
    print(f"Location: {location:20s} | Count: {row[0]:4d} | Avg Price/SqFt: Rs.{row[2]:8,.0f}" if row[2] else f"Location: {location:20s} | Count: {row[0]:4d} | No data")

# Create DataFrame and save
df = pd.DataFrame(results)
output_file = r"c:\Users\gudde\OneDrive\Desktop\Final\DB_VERIFIED_location_costs.csv"
df.to_csv(output_file, index=False)

print()
print("=" * 100)
print(f"Total Properties: {df['Count'].sum():,}")
print(f"Saved to: DB_VERIFIED_location_costs.csv")
print("=" * 100)

# Display formatted table
print()
print("DETAILED RESULTS:")
print()
for _, row in df.iterrows():
    print(f"📍 {row['Location'].upper()}")
    print(f"   Properties: {int(row['Count']):,}")
    print(f"   Avg Base Price: Rs.{row['Avg_Base_Price_Cr']:.2f} Cr")
    print(f"   Avg Price/SqFt: Rs.{row['Avg_Price_SqFt']:,.0f}")
    print(f"   Base Price Range: Rs.{row['Min_Base_Cr']:.2f} Cr - Rs.{row['Max_Base_Cr']:.2f} Cr")
    print(f"   Price/SqFt Range: Rs.{row['Min_Price_SqFt']:,.0f} - Rs.{row['Max_Price_SqFt']:,.0f}")
    print()

cur.close()
conn.close()
