"""
Load scraped Telangana data into PostgreSQL database
"""

import json
import csv
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )

def load_hierarchy_data(conn):
    """Load area hierarchy from JSON"""
    data_dir = Path(__file__).parent.parent / "scraped_data"
    
    # Find latest hierarchy file
    hier_files = list(data_dir.glob("telangana_hierarchy_*.json"))
    if not hier_files:
        print("No hierarchy data found!")
        return 0, 0
    
    latest = max(hier_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Loading hierarchy from: {latest.name}")
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cur = conn.cursor()
    mandal_count = 0
    village_count = 0
    
    for district in data.get("districts", []):
        district_name = district["district"]
        district_code = district["code"]
        
        for mandal in district.get("mandals", []):
            mandal_name = mandal["mandal"]
            mandal_code = mandal["code"]
            
            # Insert mandal
            cur.execute("""
                INSERT INTO telangana_mandals (name, code, district_name, district_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (code, district_code) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, (mandal_name, mandal_code, district_name, district_code))
            
            mandal_id = cur.fetchone()[0]
            mandal_count += 1
            
            # Insert villages
            for village in mandal.get("villages", []):
                village_name = village["name"]
                village_code = village["code"]
                
                cur.execute("""
                    INSERT INTO telangana_villages (name, code, mandal_id, mandal_name, mandal_code, district_name, district_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (code, mandal_code, district_code) DO UPDATE SET name = EXCLUDED.name
                """, (village_name, village_code, mandal_id, mandal_name, mandal_code, district_name, district_code))
                village_count += 1
    
    conn.commit()
    return mandal_count, village_count

def load_market_values(conn):
    """Load market values from cleaned CSV"""
    data_dir = Path(__file__).parent.parent / "scraped_data"
    
    # Find latest clean market values file
    mv_files = list(data_dir.glob("clean_market_values_*.csv"))
    if not mv_files:
        # Try raw file
        mv_files = list(data_dir.glob("market_values_*.json"))
        if mv_files:
            return load_market_values_from_json(conn, max(mv_files, key=lambda x: x.stat().st_mtime))
        print("No market values data found!")
        return 0
    
    latest = max(mv_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Loading market values from: {latest.name}")
    
    cur = conn.cursor()
    count = 0
    
    with open(latest, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Batch insert
    for row in rows:
        try:
            price = float(row.get('price_per_sqyd', 0))
            if price > 0:
                cur.execute("""
                    INSERT INTO telangana_market_values 
                    (district, mandal, village, classification, price_per_sqyd, rate_type, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (village_code, classification, rate_type) DO NOTHING
                """, (
                    row.get('district', ''),
                    row.get('mandal', ''),
                    row.get('village', ''),
                    row.get('classification', ''),
                    price,
                    row.get('rate_type', 'Non-Agriculture'),
                    datetime.now()
                ))
                count += 1
        except Exception as e:
            pass
    
    conn.commit()
    return count

def load_market_values_from_json(conn, filepath):
    """Load market values from JSON file"""
    print(f"📂 Loading market values from: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cur = conn.cursor()
    count = 0
    
    for record in data.get("market_values", []):
        try:
            # The effective_from field contains actual price
            price_str = record.get("effective_from", "0")
            price = float(str(price_str).replace(",", "").replace("₹", "").strip() or 0)
            
            if price > 0:
                classification = record.get("unit", "")  # unit field has classification
                cur.execute("""
                    INSERT INTO telangana_market_values 
                    (district, district_code, mandal, mandal_code, village, village_code,
                     classification, price_per_sqyd, rate_type, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (village_code, classification, rate_type) 
                    DO UPDATE SET price_per_sqyd = EXCLUDED.price_per_sqyd
                """, (
                    record.get('district', ''),
                    record.get('district_code', ''),
                    record.get('mandal', ''),
                    record.get('mandal_code', ''),
                    record.get('village', ''),
                    record.get('village_code', ''),
                    classification,
                    price,
                    record.get('rate_type', 'Non-Agriculture'),
                    datetime.now()
                ))
                count += 1
        except Exception as e:
            pass
    
    conn.commit()
    return count

def show_stats(conn):
    """Display database statistics"""
    cur = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 DATABASE STATISTICS")
    print("="*60)
    
    # Counts
    cur.execute("SELECT COUNT(*) FROM telangana_districts")
    print(f"  Districts:      {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM telangana_mandals")
    print(f"  Mandals:        {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM telangana_villages")
    print(f"  Villages:       {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM telangana_market_values")
    mv_count = cur.fetchone()[0]
    print(f"  Market Values:  {mv_count}")
    
    if mv_count > 0:
        # Price stats
        cur.execute("""
            SELECT district, COUNT(*) as cnt, 
                   MIN(price_per_sqyd) as min_p, 
                   MAX(price_per_sqyd) as max_p,
                   AVG(price_per_sqyd) as avg_p
            FROM telangana_market_values
            WHERE price_per_sqyd > 0
            GROUP BY district
            ORDER BY max_p DESC
        """)
        
        print("\n" + "-"*60)
        print("📍 PRICE DATA BY DISTRICT")
        print("-"*60)
        
        for row in cur.fetchall():
            print(f"\n  🏛️ {row[0]}")
            print(f"     Records: {row[1]}")
            print(f"     Price Range: ₹{row[2]:,.0f} - ₹{row[3]:,.0f} per Sq.Yd")
            print(f"     Average: ₹{row[4]:,.0f} per Sq.Yd")
        
        # Top 5 locations
        cur.execute("""
            SELECT village, mandal, district, MAX(price_per_sqyd) as max_price
            FROM telangana_market_values
            WHERE price_per_sqyd > 0
            GROUP BY village, mandal, district
            ORDER BY max_price DESC
            LIMIT 5
        """)
        
        print("\n" + "-"*60)
        print("🏆 TOP 5 HIGHEST PRICED LOCATIONS")
        print("-"*60)
        
        for i, row in enumerate(cur.fetchall(), 1):
            print(f"  {i}. {row[0]} ({row[1]}, {row[2]}) - ₹{row[3]:,.0f}/Sq.Yd")
    
    print("\n" + "="*60)

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║       LOAD SCRAPED DATA INTO DATABASE                             ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    conn = get_db_connection()
    print("✅ Connected to database")
    
    try:
        # Load hierarchy
        print("\n📍 Loading area hierarchy...")
        mandals, villages = load_hierarchy_data(conn)
        print(f"   ✅ Loaded {mandals} mandals, {villages} villages")
        
        # Load market values
        print("\n💰 Loading market values...")
        mv_count = load_market_values(conn)
        print(f"   ✅ Loaded {mv_count} market value records")
        
        # Show stats
        show_stats(conn)
        
    finally:
        conn.close()
        print("\n✅ Database connection closed")

if __name__ == "__main__":
    main()
