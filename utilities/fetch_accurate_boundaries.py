"""
Fetch Accurate Locality Boundaries from OpenStreetMap
=====================================================
Uses Overpass API to get suburb/neighbourhood boundaries
"""

import requests
import json
import psycopg2
import time
import os
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

def fetch_locality_boundary_overpass(location_name, lat, lng):
    """Fetch boundary from OSM Overpass API - searches for suburb/neighbourhood"""
    
    # Search in a 5km radius for the locality
    query = f"""
    [out:json][timeout:30];
    (
      // Search for suburb/neighbourhood with matching name
      relation["place"~"suburb|neighbourhood|locality"]["name"~"{location_name}",i](around:5000,{lat},{lng});
      way["place"~"suburb|neighbourhood|locality"]["name"~"{location_name}",i](around:5000,{lat},{lng});
      
      // Also try admin boundaries
      relation["boundary"="administrative"]["name"~"{location_name}",i](around:5000,{lat},{lng});
      
      // Try landuse=residential areas
      relation["landuse"~"residential|commercial"]["name"~"{location_name}",i](around:5000,{lat},{lng});
      way["landuse"~"residential|commercial"]["name"~"{location_name}",i](around:5000,{lat},{lng});
    );
    out geom;
    """
    
    try:
        headers = {
            'User-Agent': 'HyderabadPropertyIntel/1.0',
            'Accept': 'application/json'
        }
        
        r = requests.post(OVERPASS_URL, data={'data': query}, headers=headers, timeout=60)
        
        if r.status_code != 200:
            print(f"    API returned {r.status_code}")
            return None
        
        data = r.json()
        elements = data.get('elements', [])
        
        if not elements:
            return None
        
        # Find best match - prefer relations over ways
        best_element = None
        for el in elements:
            if el.get('type') == 'relation':
                best_element = el
                break
            elif el.get('type') == 'way' and not best_element:
                best_element = el
        
        if not best_element:
            best_element = elements[0]
        
        # Convert to GeoJSON
        geojson = convert_osm_to_geojson(best_element)
        
        if geojson:
            return {
                'name': best_element.get('tags', {}).get('name', location_name),
                'osm_id': best_element.get('id'),
                'osm_type': best_element.get('type'),
                'geometry': geojson
            }
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return None

def convert_osm_to_geojson(element):
    """Convert OSM element to GeoJSON geometry"""
    
    if element.get('type') == 'way':
        # Way with geometry
        geometry = element.get('geometry', [])
        if geometry:
            coords = [[p['lon'], p['lat']] for p in geometry]
            # Close polygon if needed
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            return {
                'type': 'Polygon',
                'coordinates': [coords]
            }
    
    elif element.get('type') == 'relation':
        # Relation - extract outer members
        members = element.get('members', [])
        outer_coords = []
        
        for member in members:
            if member.get('role') == 'outer' and member.get('geometry'):
                coords = [[p['lon'], p['lat']] for p in member['geometry']]
                outer_coords.extend(coords)
        
        if outer_coords:
            # Close polygon if needed
            if outer_coords[0] != outer_coords[-1]:
                outer_coords.append(outer_coords[0])
            return {
                'type': 'Polygon',
                'coordinates': [outer_coords]
            }
        
        # Try bounds if no geometry
        bounds = element.get('bounds', {})
        if bounds:
            minlat = bounds.get('minlat')
            maxlat = bounds.get('maxlat')
            minlon = bounds.get('minlon')
            maxlon = bounds.get('maxlon')
            if all([minlat, maxlat, minlon, maxlon]):
                return {
                    'type': 'Polygon',
                    'coordinates': [[
                        [minlon, minlat],
                        [maxlon, minlat],
                        [maxlon, maxlat],
                        [minlon, maxlat],
                        [minlon, minlat]
                    ]]
                }
    
    return None

def fetch_boundaries_for_all_locations():
    """Fetch boundaries for all Hyderabad locations"""
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all locations without proper boundaries
    cur.execute("""
        SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng
        FROM locations
        WHERE geom IS NOT NULL
        ORDER BY name
    """)
    
    locations = cur.fetchall()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║     ACCURATE LOCALITY BOUNDARY FETCHER                            ║
║     Source: OpenStreetMap Overpass API                            ║
╚═══════════════════════════════════════════════════════════════════╝

📍 Processing {len(locations)} locations...
    """)
    
    success = 0
    failed = 0
    all_boundaries = []
    
    for loc_id, name, lat, lng in locations:
        print(f"\n🔍 {name}...")
        
        result = fetch_locality_boundary_overpass(name, lat, lng)
        
        if result and result.get('geometry'):
            geom = result['geometry']
            
            # Update database
            try:
                cur.execute("""
                    UPDATE locations 
                    SET boundary = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                    WHERE id = %s
                """, (json.dumps(geom), loc_id))
                conn.commit()
                
                success += 1
                print(f"   ✓ Found boundary (OSM {result['osm_type']} {result['osm_id']})")
                
                # Store for GeoJSON export
                all_boundaries.append({
                    'type': 'Feature',
                    'properties': {
                        'id': loc_id,
                        'name': name,
                        'osm_id': result.get('osm_id'),
                        'osm_type': result.get('osm_type')
                    },
                    'geometry': geom
                })
                
            except Exception as e:
                print(f"   ⚠️ DB Error: {e}")
                conn.rollback()
                failed += 1
        else:
            failed += 1
            print(f"   ✗ No boundary found")
        
        time.sleep(2)  # Respect rate limits
    
    cur.close()
    conn.close()
    
    # Export to GeoJSON
    if all_boundaries:
        output_file = 'frontend/data/hyderabad_localities.geojson'
        geojson = {
            'type': 'FeatureCollection',
            'features': all_boundaries
        }
        with open(output_file, 'w') as f:
            json.dump(geojson, f, indent=2)
        print(f"\n📁 Exported to {output_file}")
    
    print(f"""
{'='*60}
📊 SUMMARY
{'='*60}
  ✓ Success: {success}
  ✗ Failed:  {failed}
  Total:     {len(locations)}
{'='*60}
    """)

def fetch_single_boundary(location_name):
    """Fetch boundary for a single location (for testing)"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng
        FROM locations
        WHERE name ILIKE %s
        LIMIT 1
    """, (f"%{location_name}%",))
    
    row = cur.fetchone()
    if not row:
        print(f"Location '{location_name}' not found")
        return
    
    loc_id, name, lat, lng = row
    print(f"\n🔍 Searching for: {name} ({lat}, {lng})")
    
    result = fetch_locality_boundary_overpass(name, lat, lng)
    
    if result:
        print(f"✓ Found: {result['osm_type']} {result['osm_id']}")
        print(f"  Geometry type: {result['geometry']['type']}")
        
        # Save to DB
        cur.execute("""
            UPDATE locations 
            SET boundary = ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
            WHERE id = %s
        """, (json.dumps(result['geometry']), loc_id))
        conn.commit()
        print(f"✓ Saved to database")
    else:
        print("✗ No boundary found")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test single location
        fetch_single_boundary(sys.argv[1])
    else:
        # Fetch all
        fetch_boundaries_for_all_locations()
