"""
SEED PRICE TRENDS: Extracts real quarterly price data from CSV.
Populates the new sophisticated price_trends schema.
"""
import pandas as pd
import psycopg2
import os, sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

# 1. Load CSV
csv_path = 'utilities/unified_data_DataType_Raghu_rows (1).csv'
print(f"Reading CSV: {csv_path}...")
df = pd.read_csv(csv_path, low_memory=False)

# 2. Clean Data
df['price'] = pd.to_numeric(df['price_per_sft'].astype(str).str.replace(',',''), errors='coerce')
df = df[(df['price'] > 500) & (df['price'] < 50000)]

df['launch_date'] = pd.to_datetime(df['project_launch_date'], format='mixed', errors='coerce')
df['config_date'] = pd.to_datetime(df['configuration_update_date'], format='mixed', errors='coerce')
df['date'] = df['launch_date'].combine_first(df['config_date'])

valid = df.dropna(subset=['price', 'date', 'areaname']).copy()
valid['quarter'] = valid['date'].dt.to_period('Q')
# Start of quarter date (e.g. 2024Q1 -> 2024-01-01)
valid['q_start_date'] = valid['quarter'].dt.start_time

# 3. Get Location IDs
cur.execute("SELECT id, name FROM locations")
loc_map = {row[1].lower().strip(): row[0] for row in cur.fetchall()}

print("Syncing trends to database...")
inserted = 0

# Group by Location + Quarter
grouped = valid.groupby(['areaname', 'quarter'])

# For interpolating gaps, we process per location
loc_groups = valid.groupby('areaname')

for area_name, group in loc_groups:
    norm_name = area_name.lower().strip()
    if norm_name not in loc_map:
        continue
    loc_id = loc_map[norm_name]
    
    # Aggregate actual data points per quarter
    # Use mean for 'average_price', min/max for range
    quarterly = group.groupby('quarter').agg({
        'price': ['mean', 'min', 'max', 'count'],
        'q_start_date': 'first'
    }).sort_index()
    
    # Flatten columns
    quarterly.columns = ['avg_price', 'min_price', 'max_price', 'count', 'date']
    
    if len(quarterly) < 1:
        continue

    # Create full date range
    min_q = quarterly.index.min()
    max_q = quarterly.index.max()
    full_range = pd.period_range(start=min_q, end=max_q, freq='Q')
    
    # Reindex over full range
    reindexed = quarterly.reindex(full_range)
    
    # Interpolate numeric columns (linear)
    reindexed['avg_price'] = reindexed['avg_price'].interpolate(method='linear')
    reindexed['min_price'] = reindexed['min_price'].interpolate(method='linear')
    reindexed['max_price'] = reindexed['max_price'].interpolate(method='linear')
    
    # Fill count with 0 for interpolated points
    reindexed['count'] = reindexed['count'].fillna(0)
    
    # Generate dates for missing quarters
    reindexed['date'] = reindexed.index.to_timestamp()
    
    # Insert rows
    for q, row in reindexed.iterrows():
        try:
            cur.execute("""
                INSERT INTO price_trends 
                (location_id, quarter, trend_date, average_price, min_price, max_price, data_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_id, quarter) DO UPDATE 
                SET average_price = EXCLUDED.average_price,
                    min_price = EXCLUDED.min_price,
                    max_price = EXCLUDED.max_price
            """, (
                loc_id, 
                str(q), 
                row['date'].date(), 
                round(float(row['avg_price']), 2),
                round(float(row['min_price']), 2),
                round(float(row['max_price']), 2),
                int(row['count'])
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting {area_name} {q}: {e}")
            conn.rollback() 
            continue

conn.commit()
cur.close()
conn.close()

print(f"\nSuccessfully seeded {inserted} quarterly trend points.")
