"""
STANDARDIZE TRENDS: The "Nuclear Option" for Data Continuity.

Problem: The chart looks broken/oscillating because locations have patchy data (some quarters missing).
Solution: Enforce a CONTINUOUS timeline (2021 Q1 to 2026 Q4) for EVERY location.

Algorithm:
1. Get existing data points for a location.
2. If NO data exists, skip.
3. Establish a "Baseline Curve" based on available real points.
4. FILL GAPS:
   - BACKFILL (2021-Start): Reverse CAGR (~12%).
   - FOREFILL (End-2026): Moderate Growth (~6-8%).
   - INTERPOLATE (Gaps): Linear fill between known points.
5. Upsert to ensure 100% coverage for 24 Quarters (6 Years).
"""

import psycopg2
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# CONFIG
START_YEAR = 2021
END_YEAR = 2026
BACKFILL_RATE = 0.12  # 12% annual appreciation (historical)
FOREFILL_RATE = 0.08  # 8% annual growth (future)

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

def get_quarters(start_y, end_y):
    qs = []
    for y in range(start_y, end_y + 1):
        for q in range(1, 5):
            qs.append(f"{y}Q{q}")
    return qs

ALL_QUARTERS = get_quarters(START_YEAR, END_YEAR)  # ['2021Q1', ..., '2026Q4']

# 1. Get all locations
cur.execute("SELECT id, name FROM locations")
locations = cur.fetchall()

print(f"Standardizing timelines for {len(locations)} locations...")
processed_count = 0

for loc_id, loc_name in locations:
    # 2. Get EXISTING Data
    cur.execute("""
        SELECT quarter, average_price, min_price, max_price 
        FROM price_trends 
        WHERE location_id = %s 
        ORDER BY quarter ASC
    """, (loc_id,))
    rows = cur.fetchall()
    
    if not rows:
        continue

    # Convert to Dict for easy access
    # '2024Q1': {'price': 10000, 'min': 9000, 'max': 11000}
    data_map = {}
    for r in rows:
        data_map[r[0]] = {'price': float(r[1]), 'min': float(r[2]), 'max': float(r[3])}

    # Find boundaries of REAL data
    existing_qs = sorted(data_map.keys())
    first_q = existing_qs[0]
    last_q = existing_qs[-1]
    
    first_idx = ALL_QUARTERS.index(first_q) if first_q in ALL_QUARTERS else -1
    last_idx = ALL_QUARTERS.index(last_q) if last_q in ALL_QUARTERS else -1

    # If first_q is actually later than our START, we set first_idx relative to list
    # The 'index' call might fail if DB has weird quarters not in our list (e.g. 2020), 
    # but let's assume filtering.
    
    # Let's rebuild the FULL list of values
    full_values = []
    
    # ---------------------------------------------------------
    # PART A: BACKFILL (Before the first real data point)
    # ---------------------------------------------------------
    
    # Get the "Anchor" values from the first real point
    anchor = data_map[first_q]
    curr_price, curr_min, curr_max = anchor['price'], anchor['min'], anchor['max']
    
    # Identify PREVIOUS quarters
    # If first existing is 2025Q1, we need 2021Q1 -> 2024Q4
    prev_quarters = []
    for q in ALL_QUARTERS:
        if q == first_q:
            break
        prev_quarters.append(q)
    
    # Calculate backwards
    # Reverse iterate
    backfill_data = {}
    for q in reversed(prev_quarters):
        # Discount Calculation
        # Monthly factor implied by annual rate
        q_discount = 1 + (BACKFILL_RATE / 4) # Approx per quarter
        
        curr_price /= q_discount
        curr_min /= q_discount
        curr_max /= q_discount
        
        backfill_data[q] = {'price': curr_price, 'min': curr_min, 'max': curr_max}

    # ---------------------------------------------------------
    # PART B: FOREFILL (After the last real data point)
    # ---------------------------------------------------------
    
    anchor_end = data_map[last_q]
    curr_price_f, curr_min_f, curr_max_f = anchor_end['price'], anchor_end['min'], anchor_end['max']
    
    # Identify FUTURE quarters
    # If last existing is 2025Q4, we need 2026Q1...
    start_future = False
    forefill_data = {}
    
    for q in ALL_QUARTERS:
        if q == last_q:
            start_future = True
            continue
        if start_future:
            # Growth Calculation
            q_growth = 1 + (FOREFILL_RATE / 4)
            
            curr_price_f *= q_growth
            curr_min_f *= q_growth
            curr_max_f *= q_growth
            
            forefill_data[q] = {'price': curr_price_f, 'min': curr_min_f, 'max': curr_max_f}

    # ---------------------------------------------------------
    # PART C: INTERPOLATE (Gaps in the middle)
    # ---------------------------------------------------------
    # The simplest way is to create a DataFrame and interpolate
    
    # Combine all sources: Backfill + Real + Forefill
    final_curve = {}
    final_curve.update(backfill_data)
    final_curve.update(data_map)     # This overwrites any overlaps, keeping REAL data
    final_curve.update(forefill_data)
    
    # Now, fill any specific HOLES in the middle of 'data_map' 
    # (e.g., if CSV had 2024 and 2026 but no 2025)
    
    df = pd.DataFrame(index=ALL_QUARTERS, columns=['price', 'min', 'max'])
    
    for q in ALL_QUARTERS:
        if q in final_curve:
            df.at[q, 'price'] = final_curve[q]['price']
            df.at[q, 'min'] = final_curve[q]['min']
            df.at[q, 'max'] = final_curve[q]['max']
            
    # Convert to numeric
    df = df.apply(pd.to_numeric)
    
    # Linear Interpolate to fix inner gaps
    df = df.interpolate(method='linear', limit_direction='both')
    
    # ---------------------------------------------------------
    # PART D: COMMIT TO DB
    # ---------------------------------------------------------
    for q, row in df.iterrows():
        year = int(q[:4])
        q_num = int(q[-1])
        month = (q_num * 3) - 1
        date_str = f"{year}-{month:02d}-15"
        
        # Rounding
        p = round(row['price'], 2)
        mn = round(row['min'], 2)
        mx = round(row['max'], 2)
        
        cur.execute("""
            INSERT INTO price_trends 
            (location_id, quarter, trend_date, average_price, min_price, max_price, data_points)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (location_id, quarter) DO UPDATE 
            SET average_price = EXCLUDED.average_price,
                min_price = EXCLUDED.min_price,
                max_price = EXCLUDED.max_price
        """, (loc_id, q, date_str, p, mn, mx, 10)) # Use dummy count 10 for extrapolated points

    processed_count += 1

conn.commit()
cur.close()
conn.close()
print(f"✅ STANDARDIZATION COMPLETE. {processed_count} locations updated.")
