
import requests
import json
import os
import psycopg2
from dotenv import load_dotenv
import time

load_dotenv()

def get_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432
    )

def fetch_location_geom(name):
    print(f"DEBUG: Fetching geometry for {name} via Nominatim...")
    url = f"https://nominatim.openstreetmap.org/search?q={name},+Hyderabad&format=json&polygon_geojson=1"
    headers = {'User-Agent': 'WestHydIntelliweb/1.0'}
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        data = r.json()
        
        if not data:
            return None, None

        # Prefer Polygon/MultiPolygon
        for result in data:
            geojson = result.get('geojson')
            if geojson and geojson.get('type') in ['Polygon', 'MultiPolygon']:
                print(f"SUCCESS: Found actual boundary for {name}")
                return geojson, 'boundary'
        
        # Fallback to Point
        first = data[0]
        return {"type": "Point", "coordinates": [float(first['lon']), float(first['lat'])]}, 'point'

    except Exception as e:
        print(f"ERROR: Nominatim error for {name}: {e}")
    
    return None, None

def main():
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, name FROM locations")
        locs = cur.fetchall()
        
        for loc_id, name in locs:
            search_name = name
            if name == "Financial District":
                search_name = "Nanakramguda Financial District"
            
            geom, gtype = fetch_location_geom(search_name)
            
            if geom:
                if gtype == 'boundary':
                    # Use generic Geometry type to handle both Polygon and MultiPolygon
                    cur.execute(
                        "UPDATE locations SET boundary = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326) WHERE id = %s",
                        (json.dumps(geom), loc_id)
                    )
                else:
                    # Create 2km approximation (approx 0.018 degrees)
                    print(f"INFO: Creating 2km approximation for {name}")
                    cur.execute(
                        "UPDATE locations SET boundary = ST_Buffer(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)::geography, 2000)::geometry WHERE id = %s",
                        (json.dumps(geom), loc_id)
                    )
                conn.commit()
                print(f"SUCCESS: Processed {name}")
            else:
                print(f"WARN: No geometry found for {name}")
            
            time.sleep(2)
            
    except Exception as e:
        print(f"FATAL: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
