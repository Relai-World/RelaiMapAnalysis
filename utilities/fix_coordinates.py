"""
Fix misplaced location coordinates with verified accurate positions.
"""
import psycopg2, os, sys
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Verified correct coordinates for misplaced locations
FIXES = {
    # === HYDERABAD LOCATIONS (were geocoded to wrong cities) ===
    38:  ("Alwal",           17.5047, 78.5249),   # Was 32.22,77.20 (Himachal!)
    61:  ("Boduppal",        17.4110, 78.5780),   # Was 13.10,77.57 (Bangalore)
    76:  ("Dammaiguda",      17.4580, 78.5670),   # Was 28.67,77.11 (Delhi!)
    160: ("Medipally",       17.4020, 78.5480),   # Was 28.61,77.03 (Delhi!)
    231: ("Turkapally",      17.5280, 78.4320),   # Was 11.06,76.94 (Tamil Nadu!)
    
    # === HYDERABAD OUTSKIRTS (slightly off) ===
    70:  ("Chevella",        17.3159, 78.1415),   # Was 78.03, correct is 78.14
    75:  ("Damarigidda",     17.2980, 78.1800),   # Slightly off, corrected
    215: ("Shadnagar",       17.0655, 78.2047),   # Was 78.19, slight correction
    
    # === ORGANO DAMARAGIDDA (outside both cities) ===
    26:  ("ORGANO DAMARAGIDDA", 17.2980, 78.1800), # Near Chevella, Hyderabad outskirts
    
    # === BANGALORE LOCATIONS (off position) ===
    306: ("Doddaballapura",  13.2940, 77.5400),   # North Bangalore township, slight fix
    325: ("Honnenahalli",    13.0500, 77.6100),   # Was 77.24, way too west
    348: ("Kodigenahalli",   13.1050, 77.5900),   # Was 13.72, too far north
    355: ("Kurubarakunte",   12.9530, 77.6890),   # Slight fix, was 77.74
    384: ("Ramanagara Town", 12.7253, 77.2805),   # Actually correct, satellite town
    417: ("Yeshwanthapura",  13.0230, 77.5510),   # Was 77.95, too far east
}

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

fixed = 0
for loc_id, (name, lat, lng) in FIXES.items():
    # Get current coords
    cur.execute("SELECT ST_Y(geom) as lat, ST_X(geom) as lng FROM locations WHERE id = %s", (loc_id,))
    old = cur.fetchone()
    if not old:
        print(f"  NOT FOUND: ID {loc_id} ({name})")
        continue
    
    old_lat, old_lng = old
    
    # Update
    cur.execute("""
        UPDATE locations 
        SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        WHERE id = %s
    """, (float(lng), float(lat), loc_id))
    
    fixed += 1
    dist_km = ((old_lat - lat)**2 + (old_lng - lng)**2)**0.5 * 111
    print(f"  FIXED: {name} (ID:{loc_id})")
    print(f"         {old_lat:.4f},{old_lng:.4f} -> {lat:.4f},{lng:.4f}  (moved {dist_km:.1f} km)")

conn.commit()

# Verify: re-run accuracy check
HYDERABAD_BBOX = {"lat_min": 17.00, "lat_max": 17.65, "lng_min": 78.10, "lng_max": 78.70}
BANGALORE_BBOX = {"lat_min": 12.65, "lat_max": 13.35, "lng_min": 77.20, "lng_max": 77.85}

cur.execute("SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng FROM locations ORDER BY name")
rows = cur.fetchall()

in_hyd = 0
in_blr = 0
outside = 0
outside_list = []

for loc_id, name, lat, lng in rows:
    if HYDERABAD_BBOX["lat_min"] <= lat <= HYDERABAD_BBOX["lat_max"] and HYDERABAD_BBOX["lng_min"] <= lng <= HYDERABAD_BBOX["lng_max"]:
        in_hyd += 1
    elif BANGALORE_BBOX["lat_min"] <= lat <= BANGALORE_BBOX["lat_max"] and BANGALORE_BBOX["lng_min"] <= lng <= BANGALORE_BBOX["lng_max"]:
        in_blr += 1
    else:
        outside += 1
        outside_list.append((loc_id, name, lat, lng))

print(f"\n{'='*55}")
print(f"  Fixed: {fixed} locations")
print(f"  In Hyderabad region:  {in_hyd}")
print(f"  In Bangalore region:  {in_blr}")
print(f"  Outside both:         {outside}")
print(f"  Accuracy:             {(in_hyd + in_blr) / len(rows) * 100:.1f}%")
print(f"{'='*55}")

if outside_list:
    print(f"\n  Still outside:")
    for loc_id, name, lat, lng in outside_list:
        print(f"    ID:{loc_id} {name} ({lat:.4f}, {lng:.4f})")

cur.close()
conn.close()
