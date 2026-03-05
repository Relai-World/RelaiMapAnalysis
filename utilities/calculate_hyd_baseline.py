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

# Get current average price across all locations
cur.execute("""
    SELECT 
        AVG(avg_price_sqft) as city_avg,
        MIN(avg_price_sqft) as city_min,
        MAX(avg_price_sqft) as city_max,
        COUNT(*) as location_count
    FROM location_costs
    WHERE avg_price_sqft > 0;
""")

result = cur.fetchone()
current_avg = float(result[0])
current_min = float(result[1])
current_max = float(result[2])
location_count = result[3]

print(f"Hyderabad Market Analysis (Based on {location_count} locations)")
print("=" * 60)
print(f"\n2026 (Current Year):")
print(f"  Average Price/sqft: ₹{current_avg:,.0f}")
print(f"  Range: ₹{current_min:,.0f} - ₹{current_max:,.0f}")

# Backcast using typical Hyderabad real estate growth rates
# Conservative estimate: 8-10% annual growth
growth_rates = {
    2025: 0.08,  # 8% growth from 2025 to 2026
    2024: 0.09,  # 9% growth from 2024 to 2025
    2023: 0.10,  # 10% growth from 2023 to 2024
}

prices = {2026: current_avg}

# Calculate backwards
for year in [2025, 2024, 2023]:
    # Price in previous year = Current price / (1 + growth_rate)
    prices[year] = prices[year + 1] / (1 + growth_rates[year])

print(f"\nHistorical Trend (Backcasted):")
for year in sorted(prices.keys()):
    print(f"  {year}: ₹{prices[year]:,.0f}/sqft")

# Create price_trends table for Hyderabad baseline
print("\nCreating Hyderabad baseline price trends in database...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS price_trends (
        id SERIAL PRIMARY KEY,
        location_id INTEGER REFERENCES locations(id),
        year INTEGER,
        avg_price_sqft NUMERIC,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_location_year UNIQUE (location_id, year)
    );
""")

# Check if we have a "Hyderabad" or "City Average" location
cur.execute("SELECT id FROM locations WHERE name ILIKE '%hyderabad%' OR name = 'City Average' LIMIT 1")
hyd_loc = cur.fetchone()

if not hyd_loc:
    # Create a virtual "Hyderabad Average" location
    cur.execute("""
        INSERT INTO locations (name, geom)
        VALUES ('Hyderabad Average', ST_SetSRID(ST_MakePoint(78.4867, 17.3850), 4326))
        RETURNING id
    """)
    hyd_loc_id = cur.fetchone()[0]
    print(f"Created 'Hyderabad Average' location (ID: {hyd_loc_id})")
else:
    hyd_loc_id = hyd_loc[0]
    print(f"Using existing location (ID: {hyd_loc_id})")

# Insert price trends
for year, price in prices.items():
    cur.execute("""
        INSERT INTO price_trends (location_id, year, avg_price_sqft)
        VALUES (%s, %s, %s)
        ON CONFLICT (location_id, year) DO UPDATE SET
        avg_price_sqft = EXCLUDED.avg_price_sqft;
    """, (hyd_loc_id, year, price))

conn.commit()
print(f"\n✓ Hyderabad baseline price trends saved to database!")
print(f"  Location ID: {hyd_loc_id}")
print(f"  Years: 2023-2026")

cur.close()
conn.close()
