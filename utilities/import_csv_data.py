
import pandas as pd
import psycopg2
import json
import os
from dotenv import load_dotenv
import math

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


def import_data():
    csv_file_path = r"c:\Users\gudde\OneDrive\Desktop\Final\utilities\unified_data_DataType_Raghu_rows (1).csv"
    
    print(f"Reading CSV file: {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Filter out rows without areaname
    df = df.dropna(subset=['areaname'])
    
    # helper to parse lat/lng
    def parse_lat_lng(json_str):
        if pd.isna(json_str): return None, None
        try:
            if isinstance(json_str, str):
                json_str = json_str.replace('""', '"').strip()
                if json_str.startswith('"') and json_str.endswith('"'):
                    json_str = json_str[1:-1]
                data = json.loads(json_str)
                return data.get('lat'), data.get('lng')
        except:
            return None, None
        return None, None

    # Pre-process columns
    # Google Place Rating (0-5) -> Sentiment (-1 to 1)
    def normalize_sentiment(rating):
        if pd.isna(rating): return 0.0
        try:
            val = float(rating)
            return max(-1.0, min(1.0, (val - 3) / 2.0))
        except:
            return 0.0

    df['sentiment_score'] = df['google_place_rating'].apply(normalize_sentiment)
    
    # Connectivity Score -> Growth
    def parse_float(val):
        if pd.isna(val): return 0.0
        try:
            return float(val)
        except:
            return 0.0

    df['growth_score'] = df['connectivity_score'].apply(parse_float)
    df['investment_score'] = df['GRID_Score'].apply(parse_float)

    # Clean infra counts
    df['hospitals'] = df['hospitals_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    df['schools'] = df['schools_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    df['metro'] = df['metro_stations_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)


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
    
    # Ensure location_costs table exists and has foreign key
    cur.execute("""
        CREATE TABLE IF NOT EXISTS location_costs (
            id SERIAL PRIMARY KEY,
            location_id INTEGER REFERENCES locations(id),
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

    print(f"Found {len(grouped)} unique areas. Starting import...")
    
    success_count = 0
    duplicates = 0
    errors = 0
    
    for area_name, group_df in grouped:
        try:
            # 1. Get Coordinates (First valid)
            lat, lng = None, None
            for _, row in group_df.iterrows():
                t_lat, t_lng = parse_lat_lng(row.get('google_place_location'))
                if t_lat and t_lng:
                    lat, lng = t_lat, t_lng
                    break
            
            if lat is None or lng is None:
                # print(f"Skipping {area_name}: No coordinates found.")
                continue

            # 2. Aggregated Scores
            avg_sentiment = group_df['sentiment_score'].mean()
            avg_growth = group_df['growth_score'].mean()
            avg_investment = group_df['investment_score'].mean()
            
            # 3. Aggregated Infra (Max or Mean? Let's take Max to show potential)
            max_hospitals = group_df['hospitals'].max()
            max_schools = group_df['schools'].max()
            max_metro = group_df['metro'].max()
            
            # 4. Aggregated Costs
            price_df = group_df.dropna(subset=['price_per_sft_clean'])
            base_price_df = group_df.dropna(subset=['base_price_clean'])
            
            prop_count = len(group_df)
            
            avg_price_sqft = price_df['price_per_sft_clean'].mean() if not price_df.empty else 0
            min_price_sqft = price_df['price_per_sft_clean'].min() if not price_df.empty else 0
            max_price_sqft = price_df['price_per_sft_clean'].max() if not price_df.empty else 0
            
            avg_base_price = base_price_df['base_price_clean'].mean() if not base_price_df.empty else 0
            min_base_price = base_price_df['base_price_clean'].min() if not base_price_df.empty else 0
            max_base_price = base_price_df['base_price_clean'].max() if not base_price_df.empty else 0


            # 5. Check Existence
            cur.execute("SELECT id FROM locations WHERE name = %s", (area_name,))
            existing = cur.fetchone()
            
            loc_id = None
            if existing:
                # Location already exists - skip entirely (don't touch existing data)
                duplicates += 1
                continue
            else:
                # Insert Location
                cur.execute("""
                    INSERT INTO locations (name, geom) 
                    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    RETURNING id
                """, (area_name, float(lng), float(lat)))
                loc_id = cur.fetchone()[0]
                
                # Insert Insights
                cur.execute("""
                    INSERT INTO location_insights (location_id, avg_sentiment_score, growth_score, investment_score)
                    VALUES (%s, %s, %s, %s)
                """, (loc_id, avg_sentiment, avg_growth, avg_investment))
                
                # Insert Infrastructure
                cur.execute("""
                    INSERT INTO location_infrastructure (location_id, hospitals, schools, metro, airports)
                    VALUES (%s, %s, %s, %s, %s)
                """, (loc_id, int(max_hospitals), int(max_schools), int(max_metro), 0))
                
                # Insert Costs
                cur.execute("""
                    INSERT INTO location_costs (location_id, location_name, property_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (loc_id, area_name, prop_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft))

                success_count += 1
                if success_count % 10 == 0:
                    print(f"Imported {success_count} areas...")
                    conn.commit()
                    
        except Exception as e:
            print(f"Error processing area {area_name}: {e}")
            conn.rollback()
            errors += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Final Count: Imported: {success_count}, Duplicates: {duplicates}, Errors: {errors}")

if __name__ == "__main__":
    import_data()
