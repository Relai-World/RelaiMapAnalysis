
import pandas as pd
import psycopg2
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
def get_db_connection():
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "post@123")
    dbname = os.getenv("DB_NAME", "real_estate_intelligence")
    port = os.getenv("DB_PORT", "5432")

    return psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=dbname,
        port=port
    )

def backfill_costs():
    csv_file_path = r"c:\Users\gudde\OneDrive\Desktop\Final\utilities\unified_data_DataType_Raghu_rows (1).csv"
    
    print(f"Reading CSV file: {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Filter out rows without areaname
    df = df.dropna(subset=['areaname'])
    
    # Pre-process Price Columns
    def parse_price(val):
        if pd.isna(val): return None
        try:
            val = str(val).replace(',', '').strip()
            return float(val)
        except:
            return None

    df['price_per_sft_clean'] = df['price_per_sft'].apply(parse_price)
    df['base_price_clean'] = df['baseprojectprice'].apply(parse_price)

    # Group by areaname
    grouped = df.groupby('areaname')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"Found {len(grouped)} unique areas. Starting backfill...")
    
    success_count = 0
    skipped = 0
    errors = 0
    
    for area_name, group_df in grouped:
        try:
            # Check if location exists
            cur.execute("SELECT id FROM locations WHERE name = %s", (area_name,))
            existing = cur.fetchone()
            
            if not existing:
                skipped += 1
                continue
            
            loc_id = existing[0]
            
            # Aggregated Costs
            price_df = group_df.dropna(subset=['price_per_sft_clean'])
            base_price_df = group_df.dropna(subset=['base_price_clean'])
            
            prop_count = len(group_df)
            
            avg_price_sqft = price_df['price_per_sft_clean'].mean() if not price_df.empty else 0
            min_price_sqft = price_df['price_per_sft_clean'].min() if not price_df.empty else 0
            max_price_sqft = price_df['price_per_sft_clean'].max() if not price_df.empty else 0
            
            avg_base_price = base_price_df['base_price_clean'].mean() if not base_price_df.empty else 0
            min_base_price = base_price_df['base_price_clean'].min() if not base_price_df.empty else 0
            max_base_price = base_price_df['base_price_clean'].max() if not base_price_df.empty else 0

            # Insert or update costs
            cur.execute("""
                INSERT INTO location_costs (location_id, location_name, property_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_id) DO UPDATE SET
                property_count = EXCLUDED.property_count,
                avg_base_price = EXCLUDED.avg_base_price,
                avg_price_sqft = EXCLUDED.avg_price_sqft,
                min_base_price = EXCLUDED.min_base_price,
                max_base_price = EXCLUDED.max_base_price,
                min_price_sqft = EXCLUDED.min_price_sqft,
                max_price_sqft = EXCLUDED.max_price_sqft;
            """, (loc_id, area_name, prop_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft))
            
            success_count += 1
            if success_count % 50 == 0:
                print(f"Backfilled {success_count} locations...")
                conn.commit()
                
        except Exception as e:
            print(f"Error processing area {area_name}: {e}")
            conn.rollback()
            errors += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Backfill Complete: Success: {success_count}, Skipped: {skipped}, Errors: {errors}")

if __name__ == "__main__":
    backfill_costs()
