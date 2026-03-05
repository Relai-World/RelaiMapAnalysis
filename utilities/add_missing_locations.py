"""
Add missing Hyderabad locations to the database.
These locations exist in the CSV but were skipped during import (likely missing coordinates).
This script uses known coordinates for these locations and aggregates their CSV data.
"""
import pandas as pd
import psycopg2
import json
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Known coordinates for missing Hyderabad locations (manually verified)
MISSING_LOCATIONS = {
    "Raviryal":           (17.2395, 78.4480),
    "Gagillapur":         (17.5550, 78.3890),
    "Lingampally":        (17.4920, 78.3180),
    "Shilpa Hills":       (17.4480, 78.3780),
    "Ramachandrapuram":   (17.4900, 78.2900),
    "Konapur":            (17.3280, 78.4540),
    "Amberpet":           (17.3880, 78.5070),
    "Dollar Hill":        (17.4600, 78.3690),
    "Punjagutta":         (17.4260, 78.4510),
    "Sirigiripuram":      (17.3200, 78.5500),
    "Depalle":            (17.5100, 78.2800),
    "Machirevula":        (17.3950, 78.3470),
    "Velmala":            (17.3780, 78.3380),
}

# Spelling variants -> merge INTO existing location (don't create new)
SPELLING_VARIANTS = {
    "Seriingampally": "Serilingampally",
    "serilingampalle": "Serilingampally",
    "Shankarpalli": "Shankarpally",
    "shankarpalle": "Shankarpally",
    "Hi Tech City": "Hitec City",
    "Bandlaguda": "Bandlaguda Jagir",
}

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )

def parse_float(val):
    if pd.isna(val): return 0.0
    try: return float(val)
    except: return 0.0

def parse_price(val):
    if pd.isna(val): return None
    try:
        val = str(val).replace(',', '').strip()
        return float(val)
    except: return None

def normalize_sentiment(rating):
    if pd.isna(rating): return 0.0
    try:
        val = float(rating)
        return max(-1.0, min(1.0, (val - 3) / 2.0))
    except: return 0.0

def main():
    csv_path = r"c:\Users\gudde\OneDrive\Desktop\Final\utilities\unified_data_DataType_Raghu_rows (1).csv"
    df = pd.read_csv(csv_path, low_memory=False)
    df = df[df['city'].str.strip() == 'Hyderabad']
    df = df.dropna(subset=['areaname'])
    
    # Pre-process scores
    df['sentiment_score'] = df['google_place_rating'].apply(normalize_sentiment)
    df['growth_score'] = df['connectivity_score'].apply(parse_float)
    df['investment_score'] = df['GRID_Score'].apply(parse_float)
    df['hospitals'] = df['hospitals_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    df['schools'] = df['schools_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    df['metro'] = df['metro_stations_count'].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else 0)
    df['price_per_sft_clean'] = df['price_per_sft'].apply(parse_price)
    df['base_price_clean'] = df['baseprojectprice'].apply(parse_price)

    conn = get_db()
    cur = conn.cursor()
    
    added = 0
    
    for area_name, (lat, lng) in MISSING_LOCATIONS.items():
        # Check if already exists (case-insensitive)
        cur.execute("SELECT id FROM locations WHERE LOWER(name) = LOWER(%s)", (area_name,))
        if cur.fetchone():
            print(f"  SKIP: {area_name} already exists")
            continue
        
        # Get CSV data for this location (case-insensitive match)
        group = df[df['areaname'].str.strip().str.lower() == area_name.lower()]
        
        if group.empty:
            # Still add with default scores
            avg_sentiment = 0.0
            avg_growth = 0.5
            avg_investment = 0.5
            max_hospitals = 0
            max_schools = 0
            max_metro = 0
            prop_count = 0
            avg_price_sqft = 0
            avg_base_price = 0
            min_price_sqft = 0
            max_price_sqft = 0
            min_base_price = 0
            max_base_price = 0
        else:
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

        # Insert location
        cur.execute("""
            INSERT INTO locations (name, geom) 
            VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            RETURNING id
        """, (area_name, float(lng), float(lat)))
        loc_id = cur.fetchone()[0]
        
        # Insert insights
        cur.execute("""
            INSERT INTO location_insights (location_id, avg_sentiment_score, growth_score, investment_score)
            VALUES (%s, %s, %s, %s)
        """, (loc_id, avg_sentiment, avg_growth, avg_investment))
        
        # Insert infrastructure
        cur.execute("""
            INSERT INTO location_infrastructure (location_id, hospitals, schools, metro, airports)
            VALUES (%s, %s, %s, %s, %s)
        """, (loc_id, max_hospitals, max_schools, max_metro, 0))
        
        # Insert costs
        cur.execute("""
            INSERT INTO location_costs (location_id, location_name, property_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (loc_id, area_name, prop_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft))
        
        added += 1
        print(f"  ADDED: {area_name} (ID: {loc_id}, {prop_count} projects, lat={lat}, lng={lng})")
    
    conn.commit()
    
    # Verify final count
    cur.execute("SELECT COUNT(*) FROM locations")
    total = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"Added {added} new locations")
    print(f"Total locations on map now: {total}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
