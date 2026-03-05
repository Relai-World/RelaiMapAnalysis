
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)

cur = conn.cursor()

# Drop and recreate the table with correct schema
print("Dropping existing location_costs table...")
cur.execute("DROP TABLE IF EXISTS location_costs CASCADE;")

print("Creating location_costs table with correct schema...")
cur.execute("""
    CREATE TABLE location_costs (
        id SERIAL PRIMARY KEY,
        location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
        location_name VARCHAR(200),
        property_count INTEGER,
        avg_base_price NUMERIC,
        avg_price_sqft NUMERIC,
        min_base_price NUMERIC,
        max_base_price NUMERIC,
        min_price_sqft NUMERIC,
        max_price_sqft NUMERIC,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_loc_cost UNIQUE (location_id)
    );
""")

conn.commit()
print("Table created successfully!")

# Verify
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'location_costs'
    ORDER BY ordinal_position;
""")

print("\nTable schema:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()
