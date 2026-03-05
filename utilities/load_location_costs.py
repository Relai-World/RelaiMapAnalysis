import pandas as pd
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

print("=" * 80)
print("LOADING LOCATION COSTS INTO DATABASE")
print("=" * 80)
print()

# Load CSV
csv_file = r"c:\Users\gudde\OneDrive\Desktop\Final\location_avg_costs_FINAL.csv"
df = pd.read_csv(csv_file)
print(f"✅ Loaded {len(df)} locations from CSV")
print()

# Connect to database
conn = get_db()
cur = conn.cursor()

# Create table
print("📊 Creating location_costs table...")
cur.execute("""
    DROP TABLE IF EXISTS location_costs CASCADE;
    
    CREATE TABLE location_costs (
        id SERIAL PRIMARY KEY,
        location_name VARCHAR(100) UNIQUE NOT NULL,
        property_count INTEGER,
        avg_base_price NUMERIC,
        avg_price_sqft NUMERIC,
        min_base_price NUMERIC,
        max_base_price NUMERIC,
        min_price_sqft NUMERIC,
        max_price_sqft NUMERIC,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()
print("✅ Table created")
print()

# Insert data
print("⬆️  Inserting location cost data...")
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO location_costs 
        (location_name, property_count, avg_base_price, avg_price_sqft, 
         min_base_price, max_base_price, min_price_sqft, max_price_sqft)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row['Location'],
        int(row['Count']),
        float(row['Avg Base Price']),
        float(row['Avg Price/SqFt']),
        float(row['Min Base Price']),
        float(row['Max Base Price']),
        float(row['Min Price/SqFt']),
        float(row['Max Price/SqFt'])
    ))
    print(f"   ✓ {row['Location']}: {int(row['Count'])} properties")

conn.commit()
print()

# Verify
cur.execute("SELECT COUNT(*) FROM location_costs;")
count = cur.fetchone()[0]

print("=" * 80)
print("🎉 SUCCESS!")
print("=" * 80)
print(f"Table: location_costs")
print(f"Total locations: {count}")
print()
print("Sample query:")
print("  SELECT * FROM location_costs WHERE location_name = 'Gachibowli';")
print("=" * 80)

cur.close()
conn.close()
