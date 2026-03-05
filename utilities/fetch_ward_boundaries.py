"""
Fetch Ward Boundaries from OpenStreetMap
========================================
Uses GHMC Ward boundaries which are accurately mapped in OSM
"""

import requests
import json
import psycopg2
import time
import os
import re
from dotenv import load_dotenv

load_dotenv()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )

def fetch_ward_boundary(location_name, lat, lng):
    """Fetch ward boundary from OSM"""
    
    # Clean location name for search
    search_name = location_name.replace("(", "").replace(")", "").strip()
    
    # Query for ward with location name
    query = f"""
    [out:json][timeout:60];
    (
      // Search for ward containing the location name
      relation["boundary"="administrative"]["name"~"{search_name}",i];
      relation["admin_level"~"9|10"]["name"~"{search_name}",i];
      
      // Also search by coordinates
      relation["boundary"="administrative"](around:2000,{lat},{lng});
    );
    out geom;
    """
    
    try:
        headers = {'User-Agent': 'HydPropertyIntel/1.0'}
        r = requests.post(OVERPASS_URL, data={'data': query}, headers=headers, timeout=90)
        
        if r.status_code != 200:
            return None
        
        data = r.json()
        elements = data.get('elements', [])
        
        # Find best match - prefer exact name match
        best_match = None
        for el in elements:
            name = el.get('tags', {}).get('name', '')
            if search_name.lower() in name.lower():
                best_match = el
                break
        
        # If no name match, use closest by coordinates
        if not best_match and elements:
            best_match = elements[0]
        
        if best_match:
            geom = extract_geometry(best_match)
            if geom:
                return {
                    'name': best_match.get('tags', {}).get('name', location_name),
                    'osm_id': best_match.get('id'),
                    'geometry': geom
                }
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return None

def extract_geometry(element):
    """Extract polygon geometry from OSM element"""
    
    if element.get('type') == 'relation':
        members = element.get('members', [])
        
        # Collect all outer ring coordinates
        outer_rings = []
        current_ring = []
        
        for member in members:
            if member.get('role') == 'outer' and member.get('geometry'):
                coords = [[p['lon'], p['lat']] for p in member['geometry']]
                current_ring.extend(coords)
        
        if current_ring:
            # Close ring if needed
            if current_ring[0] != current_ring[-1]:
                current_ring.append(current_ring[0])
            
            return {
                'type': 'Polygon',
                'coordinates': [current_ring]
            }
    
    elif element.get('type') == 'way':
        geometry = element.get('geometry', [])
        if geometry:
            coords = [[p['lon'], p['lat']] for p in geometry]
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            return {
                'type': 'Polygon',
                'coordinates': [coords]
            }
    
    return None

def fetch_all_hyderabad_wards():
    """Fetch all GHMC wards at once"""
    
    print("\n📥 Fetching all Hyderabad ward boundaries from OSM...")
    
    query = """
    [out:json][timeout:120];
    area["name"="Greater Hyderabad"]->.searchArea;
    (
      relation["boundary"="administrative"]["admin_level"~"9|10"](area.searchArea);
      relation["type"="boundary"]["name"~"Ward",i](area.searchArea);
    );
    out geom;
    """
    
    try:
        headers = {'User-Agent': 'HydPropertyIntel/1.0'}
        r = requests.post(OVERPASS_URL, data={'data': query}, headers=headers, timeout=180)
        
        if r.status_code != 200:
            print(f"Error: HTTP {r.status_code}")
            return {}
        
        data = r.json()
        elements = data.get('elements', [])
        
        print(f"✓ Found {len(elements)} ward boundaries")
        
        wards = {}
        for el in elements:
            name = el.get('tags', {}).get('name', '')
            geom = extract_geometry(el)
            if name and geom:
                # Extract location name from ward name (e.g., "Ward 105 Gachibowli" -> "Gachibowli")
                clean_name = re.sub(r'Ward\s*\d+\s*', '', name).strip()
                if clean_name:
                    wards[clean_name.lower()] = {
                        'ward_name': name,
                        'geometry': geom,
                        'osm_id': el.get('id')
                    }
        
        return wards
        
    except Exception as e:
        print(f"Error: {e}")
        return {}

def update_location_boundaries():
    """Update all locations with ward boundaries"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║     HYDERABAD WARD BOUNDARY FETCHER                               ║
║     Source: OpenStreetMap GHMC Wards                              ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # First, fetch all wards
    wards = fetch_all_hyderabad_wards()
    
    if not wards:
        print("No wards found! Trying individual fetch...")
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all locations
    cur.execute("""
        SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng
        FROM locations
        WHERE geom IS NOT NULL
        ORDER BY name
    """)
    locations = cur.fetchall()
    
    print(f"\n📍 Matching {len(locations)} locations to ward boundaries...\n")
    
    success = 0
    individual_fetch = 0
    failed = 0
    results = []
    
    for loc_id, name, lat, lng in locations:
        # Try to match with pre-fetched wards
        matched = False
        name_lower = name.lower()
        
        for ward_key, ward_data in wards.items():
            if ward_key in name_lower or name_lower in ward_key:
                # Found match!
                try:
                    cur.execute("""
                        UPDATE locations 
                        SET boundary = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                        WHERE id = %s
                    """, (json.dumps(ward_data['geometry']), loc_id))
                    conn.commit()
                    
                    success += 1
                    matched = True
                    print(f"✓ {name} -> {ward_data['ward_name']}")
                    
                    results.append({
                        'type': 'Feature',
                        'properties': {'id': loc_id, 'name': name, 'ward': ward_data['ward_name']},
                        'geometry': ward_data['geometry']
                    })
                    break
                except Exception as e:
                    print(f"✗ {name}: DB error - {e}")
                    conn.rollback()
        
        if not matched:
            # Try individual fetch
            print(f"  {name} - trying individual fetch...")
            result = fetch_ward_boundary(name, lat, lng)
            
            if result and result.get('geometry'):
                try:
                    cur.execute("""
                        UPDATE locations 
                        SET boundary = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                        WHERE id = %s
                    """, (json.dumps(result['geometry']), loc_id))
                    conn.commit()
                    
                    individual_fetch += 1
                    print(f"  ✓ {name} -> {result['name']}")
                    
                    results.append({
                        'type': 'Feature',
                        'properties': {'id': loc_id, 'name': name, 'ward': result['name']},
                        'geometry': result['geometry']
                    })
                except Exception as e:
                    print(f"  ✗ {name}: DB error - {e}")
                    conn.rollback()
                    failed += 1
                
                time.sleep(2)  # Rate limit
            else:
                failed += 1
                print(f"  ✗ {name}: No boundary found")
    
    cur.close()
    conn.close()
    
    # Export GeoJSON
    if results:
        output_file = 'frontend/data/hyderabad_localities.geojson'
        geojson = {'type': 'FeatureCollection', 'features': results}
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"\n📁 Exported {len(results)} boundaries to {output_file}")
    
    print(f"""
{'='*60}
📊 SUMMARY
{'='*60}
  ✓ Ward match:       {success}
  ✓ Individual fetch: {individual_fetch}
  ✗ Not found:        {failed}
  Total:              {len(locations)}
{'='*60}
    """)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test single location
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, ST_Y(geom), ST_X(geom) FROM locations WHERE name ILIKE %s", (f"%{sys.argv[1]}%",))
        row = cur.fetchone()
        if row:
            print(f"Testing: {row[1]} ({row[2]}, {row[3]})")
            result = fetch_ward_boundary(row[1], row[2], row[3])
            if result:
                print(f"Found: {result['name']} (OSM ID: {result['osm_id']})")
                print(f"Geometry type: {result['geometry']['type']}")
            else:
                print("No boundary found")
        cur.close()
        conn.close()
    else:
        update_location_boundaries()
