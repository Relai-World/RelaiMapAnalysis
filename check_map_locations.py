import psycopg2, os, sys, json
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'post@123'),
    dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
    port=os.getenv('DB_PORT', '5432'),
    sslmode='prefer'
)
cur = conn.cursor()

# ── 1. Check duplicate names in locations table ─────────────
print("="*65)
print("DUPLICATE NAMES IN locations TABLE (Hyderabad)")
print("="*65)
cur.execute("""
    SELECT name, COUNT(*) as cnt,
           array_agg(id ORDER BY id) as ids
    FROM locations
    WHERE city ILIKE '%Hyderabad%'
    GROUP BY name
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC, name;
""")
dupes = cur.fetchall()
if dupes:
    for name, cnt, ids in dupes:
        print(f"  '{name}'  appears {cnt} times  — IDs: {ids}")
else:
    print("  No duplicate names found in locations table.")

# ── 2. Check geom for Appa Junction & Madhapur ──────────────
print(f"\n{'='*65}")
print("GEOM DATA FOR 'Appa Junction' & 'Madhapur' in locations table")
print("="*65)
cur.execute("""
    SELECT id, name, city,
           ST_AsGeoJSON(geom)::json AS geom_json
    FROM locations
    WHERE city ILIKE '%Hyderabad%'
      AND (name ILIKE '%appa junction%' OR name ILIKE '%madhapur%')
    ORDER BY name, id;
""")
rows = cur.fetchall()
for lid, name, city, geom in rows:
    if geom and geom.get('coordinates'):
        coords = geom['coordinates']
        print(f"  ID={lid}  '{name}'  coords: lat={coords[1]}, lng={coords[0]}")
    else:
        print(f"  ID={lid}  '{name}'  NO GEOM")

# ── 3. Check google_place_location in properties_final ───────
print(f"\n{'='*65}")
print("google_place_location FOR 'Appa Junction' & 'Madhapur' in properties_final")
print("="*65)
for area in ['Appa Junction', 'Madhapur']:
    cur.execute("""
        SELECT areaname, google_place_location, COUNT(*) as cnt
        FROM properties_final
        WHERE areaname ILIKE %s
          AND city ILIKE '%%Hyderabad%%'
          AND google_place_location IS NOT NULL
        GROUP BY areaname, google_place_location
        ORDER BY cnt DESC
        LIMIT 10;
    """, (f'%{area}%',))
    rows = cur.fetchall()
    print(f"\n  '{area}':")
    if rows:
        for aname, gpl, cnt in rows:
            print(f"    areaname='{aname}'  val={str(gpl)[:80]}  ({cnt} props)")
    else:
        print(f"    No data found.")

# ── 4. Check all locations with DUPLICATE coordinates ────────
print(f"\n{'='*65}")
print("ALL LOCATIONS WITH SAME COORDS (potential map overlaps)")
print("="*65)
cur.execute("""
    SELECT ST_AsText(geom) as coord_text,
           array_agg(name ORDER BY name) as names,
           COUNT(*) as cnt
    FROM locations
    WHERE city ILIKE '%Hyderabad%'
      AND geom IS NOT NULL
    GROUP BY ST_AsText(geom)
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC;
""")
coord_dupes = cur.fetchall()
if coord_dupes:
    print(f"  Found {len(coord_dupes)} sets of locations sharing the same coordinates:")
    for coords, names, cnt in coord_dupes:
        print(f"    coords={coords}  →  {names}")
else:
    print("  No duplicate coordinates found.")

cur.close()
conn.close()
