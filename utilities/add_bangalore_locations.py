"""
Add ALL missing Bangalore locations using Nominatim geocoding for coordinates.
"""
import pandas as pd
import psycopg2
import json
import os
import sys
import time
import requests as req
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )

def geocode_location(name):
    """Geocode a Bangalore location using Nominatim"""
    # Clean up the name for geocoding
    clean_name = name.strip()
    # Remove common suffixes that confuse geocoding
    for suffix in [' HOBLI', ' ZONE', ' Hobli', ' Village', ' Road']:
        if clean_name.endswith(suffix):
            clean_name = clean_name[:-len(suffix)].strip()
    
    queries = [
        f"{clean_name}, Bangalore, Karnataka, India",
        f"{clean_name}, Bengaluru, Karnataka, India",
        f"{clean_name}, Karnataka, India",
    ]
    
    headers = {"User-Agent": "RealEstateIntelPlatform/1.0"}
    
    for query in queries:
        try:
            resp = req.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                headers=headers,
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    # Validate: must be in South India range
                    if 11.5 < lat < 14.5 and 76.5 < lon < 78.5:
                        return lat, lon
            time.sleep(1.1)  # Respect Nominatim rate limit
        except Exception as e:
            pass
    
    return None, None

def parse_lat_lng(json_str):
    if pd.isna(json_str): return None, None
    try:
        if isinstance(json_str, str):
            json_str = json_str.replace('""', '"').strip()
            if json_str.startswith('"') and json_str.endswith('"'):
                json_str = json_str[1:-1]
            data = json.loads(json_str)
            lat = data.get('lat')
            lng = data.get('lng')
            if lat and lng:
                lat, lng = float(lat), float(lng)
                if 11.5 < lat < 14.5 and 76.5 < lng < 78.5:
                    return lat, lng
    except:
        pass
    return None, None

def parse_float(val):
    if pd.isna(val): return 0.0
    try: return float(val)
    except: return 0.0

def parse_price(val):
    if pd.isna(val): return None
    try: return float(str(val).replace(',', '').strip())
    except: return None

def normalize_sentiment(rating):
    if pd.isna(rating): return 0.0
    try: return max(-1.0, min(1.0, (float(rating) - 3) / 2.0))
    except: return 0.0

def main():
    csv_path = r"c:\Users\gudde\OneDrive\Desktop\Final\utilities\unified_data_DataType_Raghu_rows (1).csv"
    df = pd.read_csv(csv_path, low_memory=False)
    
    blr_df = df[df['city'].str.strip().isin(['Bangalore', 'Bengaluru'])].copy()
    blr_df = blr_df.dropna(subset=['areaname'])
    
    # Pre-process
    blr_df['sentiment_score'] = blr_df['google_place_rating'].apply(normalize_sentiment)
    blr_df['growth_score'] = blr_df['connectivity_score'].apply(parse_float)
    blr_df['investment_score'] = blr_df['GRID_Score'].apply(parse_float)
    blr_df['hospitals'] = blr_df['hospitals_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    blr_df['schools'] = blr_df['schools_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    blr_df['metro'] = blr_df['metro_stations_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    blr_df['price_per_sft_clean'] = blr_df['price_per_sft'].apply(parse_price)
    blr_df['base_price_clean'] = blr_df['baseprojectprice'].apply(parse_price)
    
    grouped = blr_df.groupby(blr_df['areaname'].str.strip())
    
    conn = get_db()
    cur = conn.cursor()
    
    added = 0
    skipped_exists = 0
    skipped_no_coords = 0
    geocoded_count = 0
    
    total_groups = len(grouped)
    print(f"Processing {total_groups} Bangalore area groups...")
    
    for idx, (area_name, group) in enumerate(grouped):
        area_name = area_name.strip()
        
        # Check if already exists
        cur.execute("SELECT id FROM locations WHERE LOWER(name) = LOWER(%s)", (area_name,))
        if cur.fetchone():
            skipped_exists += 1
            continue
        
        # Try CSV coordinates first
        lat, lng = None, None
        for _, row in group.iterrows():
            t_lat, t_lng = parse_lat_lng(row.get('google_place_location'))
            if t_lat and t_lng:
                lat, lng = t_lat, t_lng
                break
        
        if lat is None:
            for _, row in group.iterrows():
                t_lat, t_lng = parse_lat_lng(row.get('google_maps_location'))
                if t_lat and t_lng:
                    lat, lng = t_lat, t_lng
                    break
        
        # If still no coords, geocode
        if lat is None:
            lat, lng = geocode_location(area_name)
            if lat:
                geocoded_count += 1
        
        if lat is None or lng is None:
            skipped_no_coords += 1
            print(f"  [{idx+1}/{total_groups}] SKIP (no coords): {area_name}")
            continue
        
        # Aggregate
        avg_sentiment = float(group['sentiment_score'].mean())
        avg_growth = float(group['growth_score'].mean())
        avg_investment = float(group['investment_score'].mean())
        max_hospitals = int(group['hospitals'].max())
        max_schools = int(group['schools'].max())
        max_metro = int(group['metro'].max())
        prop_count = len(group)
        
        price_df = group.dropna(subset=['price_per_sft_clean'])
        base_df = group.dropna(subset=['base_price_clean'])
        
        avg_price_sqft = float(price_df['price_per_sft_clean'].mean()) if not price_df.empty else 0
        min_price_sqft = float(price_df['price_per_sft_clean'].min()) if not price_df.empty else 0
        max_price_sqft = float(price_df['price_per_sft_clean'].max()) if not price_df.empty else 0
        avg_base_price = float(base_df['base_price_clean'].mean()) if not base_df.empty else 0
        min_base_price = float(base_df['base_price_clean'].min()) if not base_df.empty else 0
        max_base_price = float(base_df['base_price_clean'].max()) if not base_df.empty else 0

        try:
            cur.execute("""
                INSERT INTO locations (name, geom) 
                VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                RETURNING id
            """, (area_name, float(lng), float(lat)))
            loc_id = cur.fetchone()[0]
            
            cur.execute("""
                INSERT INTO location_insights (location_id, avg_sentiment_score, growth_score, investment_score)
                VALUES (%s, %s, %s, %s)
            """, (loc_id, avg_sentiment, avg_growth, avg_investment))
            
            cur.execute("""
                INSERT INTO location_infrastructure (location_id, hospitals, schools, metro, airports)
                VALUES (%s, %s, %s, %s, %s)
            """, (loc_id, max_hospitals, max_schools, max_metro, 0))
            
            cur.execute("""
                INSERT INTO location_costs (location_id, location_name, property_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (loc_id, area_name, prop_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft))
            
            added += 1
            print(f"  [{idx+1}/{total_groups}] ADDED: {area_name} (ID:{loc_id}, {prop_count} projects, {lat:.4f}, {lng:.4f})")
            
            if added % 20 == 0:
                conn.commit()
                
        except Exception as e:
            print(f"  [{idx+1}/{total_groups}] ERROR: {area_name}: {e}")
            conn.rollback()
    
    conn.commit()
    
    cur.execute("SELECT COUNT(*) FROM locations")
    total = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"\n{'='*55}")
    print(f"  ADDED:              {added}")
    print(f"  GEOCODED:           {geocoded_count}")
    print(f"  ALREADY EXISTED:    {skipped_exists}")
    print(f"  SKIPPED (no coords):{skipped_no_coords}")
    print(f"  TOTAL ON MAP NOW:   {total}")
    print(f"{'='*55}")

if __name__ == "__main__":
    main()
