"""
Fetch Boundaries for Telangana Locations from OpenStreetMap
============================================================
Uses Nominatim API to get village/mandal boundaries
"""

import requests
import json
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )

def ensure_geometry_columns():
    """Add geometry columns to telangana tables if not exist"""
    conn = get_db()
    cur = conn.cursor()
    
    # Add boundary column to villages
    cur.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='telangana_villages' AND column_name='boundary') THEN
                ALTER TABLE telangana_villages ADD COLUMN boundary geometry(Geometry, 4326);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='telangana_villages' AND column_name='centroid') THEN
                ALTER TABLE telangana_villages ADD COLUMN centroid geometry(Point, 4326);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='telangana_mandals' AND column_name='boundary') THEN
                ALTER TABLE telangana_mandals ADD COLUMN boundary geometry(Geometry, 4326);
            END IF;
        END $$;
    """)
    
    # Create spatial index
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_telangana_villages_boundary 
        ON telangana_villages USING GIST(boundary);
        CREATE INDEX IF NOT EXISTS idx_telangana_villages_centroid 
        ON telangana_villages USING GIST(centroid);
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Geometry columns ready")

def fetch_boundary_from_nominatim(village_name, mandal_name, district_name):
    """Fetch boundary from Nominatim"""
    headers = {
        'User-Agent': 'TelanganaPropertyIntel/1.0 (educational project)',
        'Accept': 'application/json'
    }
    
    # Try different search queries
    search_queries = [
        f"{village_name}, {mandal_name}, {district_name}, Telangana, India",
        f"{village_name}, {district_name}, Telangana, India",
        f"{village_name}, Telangana, India",
    ]
    
    for query in search_queries:
        try:
            params = {
                'q': query,
                'format': 'json',
                'polygon_geojson': 1,
                'limit': 1
            }
            
            r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=30)
            
            if r.status_code != 200:
                continue
            
            data = r.json()
            
            if not data:
                continue
            
            result = data[0]
            geojson = result.get('geojson')
            lat = float(result.get('lat', 0))
            lon = float(result.get('lon', 0))
            
            # Check if we got a polygon
            if geojson and geojson.get('type') in ['Polygon', 'MultiPolygon']:
                return {
                    'boundary': geojson,
                    'centroid': {'type': 'Point', 'coordinates': [lon, lat]},
                    'type': 'polygon'
                }
            
            # Return just the point
            if lat and lon:
                return {
                    'boundary': None,
                    'centroid': {'type': 'Point', 'coordinates': [lon, lat]},
                    'type': 'point'
                }
                
        except Exception as e:
            pass
    
    return None

def fetch_boundaries_for_district(district_name, limit=None):
    """Fetch boundaries for all villages in a district"""
    conn = get_db()
    cur = conn.cursor()
    
    # Get villages without boundaries
    query = """
        SELECT id, name, mandal_name, district_name 
        FROM telangana_villages 
        WHERE district_name = %s AND centroid IS NULL
        ORDER BY name
    """
    if limit:
        query += f" LIMIT {limit}"
    
    cur.execute(query, (district_name,))
    villages = cur.fetchall()
    
    print(f"\n📍 Fetching boundaries for {len(villages)} villages in {district_name}")
    
    success = 0
    points = 0
    failed = 0
    
    for village_id, village_name, mandal_name, dist_name in villages:
        result = fetch_boundary_from_nominatim(village_name, mandal_name, dist_name)
        
        if result:
            if result['boundary']:
                cur.execute("""
                    UPDATE telangana_villages 
                    SET boundary = ST_GeomFromGeoJSON(%s),
                        centroid = ST_GeomFromGeoJSON(%s)
                    WHERE id = %s
                """, (json.dumps(result['boundary']), json.dumps(result['centroid']), village_id))
                success += 1
                print(f"  ✓ {village_name} - polygon found")
            elif result['centroid']:
                cur.execute("""
                    UPDATE telangana_villages 
                    SET centroid = ST_GeomFromGeoJSON(%s)
                    WHERE id = %s
                """, (json.dumps(result['centroid']), village_id))
                points += 1
                print(f"  • {village_name} - point only")
        else:
            failed += 1
            print(f"  ✗ {village_name} - not found")
        
        conn.commit()
        time.sleep(1.5)  # Respect rate limits
    
    cur.close()
    conn.close()
    
    return {'polygons': success, 'points': points, 'failed': failed}

def fetch_all_boundaries(limit_per_district=10):
    """Fetch boundaries for all districts"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT district_name FROM telangana_villages ORDER BY district_name")
    districts = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║     TELANGANA LOCATION BOUNDARY FETCHER                           ║
║     Source: OpenStreetMap/Nominatim                               ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    total_stats = {'polygons': 0, 'points': 0, 'failed': 0}
    
    for district in districts:
        stats = fetch_boundaries_for_district(district, limit=limit_per_district)
        total_stats['polygons'] += stats['polygons']
        total_stats['points'] += stats['points']
        total_stats['failed'] += stats['failed']
    
    print("\n" + "="*60)
    print("📊 BOUNDARY FETCH COMPLETE")
    print("="*60)
    print(f"  Polygons found: {total_stats['polygons']}")
    print(f"  Points only:    {total_stats['points']}")
    print(f"  Not found:      {total_stats['failed']}")
    print("="*60)

def export_boundaries_geojson(district_name=None, output_file=None):
    """Export boundaries as GeoJSON file"""
    conn = get_db()
    cur = conn.cursor()
    
    if district_name:
        cur.execute("""
            SELECT name, mandal_name, district_name, 
                   ST_AsGeoJSON(COALESCE(boundary, ST_Buffer(centroid::geography, 1000)::geometry)) as geom
            FROM telangana_villages
            WHERE district_name = %s AND (boundary IS NOT NULL OR centroid IS NOT NULL)
        """, (district_name,))
    else:
        cur.execute("""
            SELECT name, mandal_name, district_name,
                   ST_AsGeoJSON(COALESCE(boundary, ST_Buffer(centroid::geography, 1000)::geometry)) as geom
            FROM telangana_villages
            WHERE boundary IS NOT NULL OR centroid IS NOT NULL
        """)
    
    rows = cur.fetchall()
    
    features = []
    for row in rows:
        if row[3]:
            features.append({
                "type": "Feature",
                "properties": {
                    "village": row[0],
                    "mandal": row[1],
                    "district": row[2]
                },
                "geometry": json.loads(row[3])
            })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    if not output_file:
        output_file = f"telangana_boundaries_{district_name or 'all'}.geojson"
    
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"✅ Exported {len(features)} boundaries to {output_file}")
    
    cur.close()
    conn.close()
    
    return output_file

def get_boundary_stats():
    """Get current boundary statistics"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM telangana_villages")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM telangana_villages WHERE boundary IS NOT NULL")
    with_boundary = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM telangana_villages WHERE centroid IS NOT NULL")
    with_centroid = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"""
📊 BOUNDARY STATISTICS
========================
  Total villages:      {total}
  With polygon:        {with_boundary}
  With centroid only:  {with_centroid - with_boundary}
  Without location:    {total - with_centroid}
    """)
    
    return {
        'total': total,
        'with_boundary': with_boundary,
        'with_centroid': with_centroid,
        'without_location': total - with_centroid
    }

if __name__ == "__main__":
    import sys
    
    # Ensure columns exist
    ensure_geometry_columns()
    
    # Show current stats
    get_boundary_stats()
    
    # Fetch boundaries (limited for demo)
    if len(sys.argv) > 1 and sys.argv[1] == '--fetch':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        fetch_all_boundaries(limit_per_district=limit)
    
    # Export to GeoJSON
    if len(sys.argv) > 1 and sys.argv[1] == '--export':
        district = sys.argv[2] if len(sys.argv) > 2 else None
        export_boundaries_geojson(district)
