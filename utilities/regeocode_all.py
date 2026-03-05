"""
Re-geocode ALL 414 locations to ensure each pin is exactly on the right neighborhood.
Uses Nominatim with city-specific queries for maximum accuracy.
"""
import psycopg2, os, sys, time
import requests as req
import pandas as pd
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Load CSV to know which city each location belongs to
csv_path = r"c:\Users\gudde\OneDrive\Desktop\Final\utilities\unified_data_DataType_Raghu_rows (1).csv"
df = pd.read_csv(csv_path, low_memory=False)

blr_names = set(df[df['city'].str.strip().isin(['Bangalore','Bengaluru'])]['areaname'].dropna().str.strip().str.lower().unique())
hyd_names = set(df[df['city'].str.strip() == 'Hyderabad']['areaname'].dropna().str.strip().str.lower().unique())

def get_city(name):
    n = name.lower().strip()
    if n in hyd_names and n not in blr_names:
        return "Hyderabad"
    elif n in blr_names and n not in hyd_names:
        return "Bangalore"
    elif n in hyd_names and n in blr_names:
        # In both — check current coords to decide
        return "BOTH"
    else:
        return "UNKNOWN"

def geocode(name, city):
    """Geocode a location with city context"""
    clean = name.strip()
    # Remove common suffixes
    for suffix in [' HOBLI', ' ZONE', ' Hobli', ' Village', ' Road', ' Main Road']:
        if clean.upper().endswith(suffix.upper()):
            clean = clean[:len(clean)-len(suffix)].strip()
    
    if city == "Hyderabad":
        queries = [
            f"{clean}, Hyderabad, Telangana, India",
            f"{clean}, Secunderabad, Telangana, India",
            f"{clean}, Rangareddy, Telangana, India",
            f"{clean}, Medchal, Telangana, India",
        ]
        lat_range = (16.9, 17.8)
        lng_range = (78.0, 78.8)
    else:
        queries = [
            f"{clean}, Bangalore, Karnataka, India",
            f"{clean}, Bengaluru, Karnataka, India",
            f"{clean}, Bengaluru Urban, Karnataka, India",
            f"{clean}, Ramanagara, Karnataka, India",
        ]
        lat_range = (12.5, 13.5)
        lng_range = (77.0, 78.0)
    
    headers = {"User-Agent": "RealEstateIntelPlatform/2.0"}
    
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
                    if lat_range[0] < lat < lat_range[1] and lng_range[0] < lon < lng_range[1]:
                        return lat, lon
            time.sleep(1.05)  # Respect rate limit
        except:
            time.sleep(1.05)
    
    return None, None

def main():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()
    
    cur.execute("SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng FROM locations ORDER BY id")
    rows = cur.fetchall()
    
    total = len(rows)
    updated = 0
    unchanged = 0
    failed = 0
    
    print(f"Re-geocoding ALL {total} locations for precise accuracy...")
    print(f"Estimated time: ~{total * 1.2 / 60:.0f} minutes\n")
    
    for i, (loc_id, name, old_lat, old_lng) in enumerate(rows):
        city = get_city(name)
        
        if city == "UNKNOWN" or city == "BOTH":
            # Determine from current coords
            if 16.9 < old_lat < 17.8:
                city = "Hyderabad"
            else:
                city = "Bangalore"
        
        new_lat, new_lng = geocode(name, city)
        
        if new_lat is None:
            failed += 1
            print(f"  [{i+1}/{total}] SKIP: {name} (no geocode result)")
            continue
        
        # Calculate distance from old position
        dist_km = (((old_lat - new_lat) * 111)**2 + ((old_lng - new_lng) * 111 * 0.9)**2)**0.5
        
        if dist_km < 0.5:
            # Less than 500m difference, already accurate
            unchanged += 1
            continue
        
        # Update the coordinates
        cur.execute("""
            UPDATE locations 
            SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            WHERE id = %s
        """, (float(new_lng), float(new_lat), loc_id))
        
        updated += 1
        print(f"  [{i+1}/{total}] MOVED: {name} ({dist_km:.1f} km shift)")
        
        if updated % 25 == 0:
            conn.commit()
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\n{'='*55}")
    print(f"  Total locations:   {total}")
    print(f"  Updated (moved):   {updated}")
    print(f"  Already accurate:  {unchanged}")
    print(f"  Could not geocode: {failed}")
    print(f"{'='*55}")

if __name__ == "__main__":
    main()
