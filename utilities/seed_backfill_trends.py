"""
SEED BACKFILL TRENDS: 
Algorithmic back-calculation of historical price trends for locations 
that only have recent (2025/2026) data.

Methodology:
1. Identify locations with 2025 data but missing 2021-2024 history.
2. Apply Reverse CAGR (Compound Annual Growth Rate) of ~12% to estimate past prices.
3. Inject these estimated quarters into the database.
"""

import psycopg2
import os
import random
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION
GROWTH_RATE_MEAN = 0.12  # 12% YoY Growth
GROWTH_VARIANCE = 0.03   # +/- 3% variance for organic look
TARGET_START_YEAR = 2021

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

def get_missing_years(loc_id):
    cur.execute("""
        SELECT DISTINCT substring(quarter from 1 for 4) as year 
        FROM price_trends 
        WHERE location_id = %s
    """, (loc_id,))
    existing_years = {int(row[0]) for row in cur.fetchall()}
    
    # We only care if we have recent data (2025 or 2026) but no past data
    has_recent = 2025 in existing_years or 2026 in existing_years
    if not has_recent:
        return []
        
    missing = []
    for y in range(TARGET_START_YEAR, 2025):
        if y not in existing_years:
            missing.append(y)
    
    # Return missing years ONLY if we need to backfill (i.e., list is not empty)
    # and we have a base year to calculate FROM (2025)
    if missing and 2025 in existing_years:
        return sorted(missing, reverse=True) # Work backwards: 2024, 2023...
    return []

def get_base_price_2025(loc_id):
    # Get average price for Q1 2025 as the anchor
    cur.execute("""
        SELECT average_price, min_price, max_price 
        FROM price_trends 
        WHERE location_id = %s AND quarter LIKE '2025%%'
        ORDER BY quarter ASC 
        LIMIT 1
    """, (loc_id,))
    return cur.fetchone()

# 1. Get all locations
cur.execute("SELECT id, name FROM locations")
locations = cur.fetchall()

total_filled = 0

print(f"Analyzing {len(locations)} locations for backfilling...")

for loc_id, loc_name in locations:
    missing_years = get_missing_years(loc_id)
    
    if not missing_years:
        continue
        
    base_data = get_base_price_2025(loc_id)
    if not base_data:
        continue
        
    curr_price, curr_min, curr_max = map(float, base_data)
    
    print(f"  > Backfilling {loc_name}: {missing_years} (Base 2025: ₹{curr_price:,.0f})")
    
    # Iterate backwards (2024 -> 2023 -> 2021)
    for year in missing_years:
        # Calculate dynamic growth rate for this year (e.g. 0.10 to 0.14)
        rate = GROWTH_RATE_MEAN + random.uniform(-GROWTH_VARIANCE, GROWTH_VARIANCE)
        discount_factor = 1 + rate
        
        # Reverse calculate
        prev_price = curr_price / discount_factor
        prev_min = curr_min / discount_factor
        prev_max = curr_max / discount_factor
        
        # Inject 4 Quarters for this year
        for q in range(1, 5):
            quarter = f"{year}Q{q}"
            
            # Intra-year smoothing (Q1 is cheaper than Q4)
            # We calculated 'prev_price' as the Year Average. 
            # Let's say Q1 is 98% of Avg, Q4 is 102% of Avg.
            q_factor = 0.98 + (0.01 * q) 
            
            final_price = round(prev_price * q_factor, 2)
            final_min = round(prev_min * q_factor, 2)
            final_max = round(prev_max * q_factor, 2)
            
            # Valid date
            month = (q * 3) - 1
            date_str = f"{year}-{month:02d}-15"
            
            cur.execute("""
                INSERT INTO price_trends 
                (location_id, quarter, trend_date, average_price, min_price, max_price, data_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_id, quarter) DO NOTHING
            """, (loc_id, quarter, date_str, final_price, final_min, final_max, 0)) 
            # Data points = 0 indicates estimated/interpolated
            
        # Update current for next iteration backwards
        curr_price = prev_price
        curr_min = prev_min
        curr_max = prev_max
        total_filled += 1

conn.commit()
cur.close()
conn.close()

print(f"\n✅ BACKFILL COMPLETE! Added {total_filled * 4} quarterly data points.")
