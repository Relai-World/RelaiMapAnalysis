"""
Clean up: Remove admin zones, merge duplicates, fix entries.
"""
import psycopg2, os, sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

# Get all FK tables
cur.execute("""
    SELECT tc.table_name, kcu.column_name 
    FROM information_schema.table_constraints tc 
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name 
    JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name 
    WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'locations'
""")
fk_tables = cur.fetchall()

def delete_location(loc_id, name, reason):
    for table, col in fk_tables:
        cur.execute(f"DELETE FROM {table} WHERE {col} = %s", (loc_id,))
    cur.execute("DELETE FROM locations WHERE id = %s", (loc_id,))
    print(f"  REMOVED: ID:{loc_id:>4} {name:<45} [{reason}]")

# ==========================================
# 1. REMOVE ADMIN ZONES (not real neighborhoods)
# ==========================================
admin_zone_ids = [
    280,  # Begur Hobli
    281,  # Beguru Hobli
    275,  # BIDARAHALLI HOBLI
    333,  # K.R.PURAM HOBLI
    346,  # Kengeri Hobli
    336,  # KR Puram Hobli
    356,  # MAHADEVAPURA ZONE
    377,  # Puram Hobli
    393,  # Sarjapura Hobli
    405,  # Uttarahalli Hobli
    406,  # VARTHUR HOBLI
    413,  # YELAHANKA ZONE
]
print("=== REMOVING ADMIN ZONES ===")
for lid in admin_zone_ids:
    cur.execute("SELECT name FROM locations WHERE id = %s", (lid,))
    row = cur.fetchone()
    if row:
        delete_location(lid, row[0], "ADMIN_ZONE")

# ==========================================
# 2. REMOVE NON-LOCATION ENTRIES
# ==========================================
print("\n=== REMOVING NON-LOCATIONS ===")
non_location_ids = [
    279,  # Banashankari 6th Stage 10th Block (too specific sub-block)
]
for lid in non_location_ids:
    cur.execute("SELECT name FROM locations WHERE id = %s", (lid,))
    row = cur.fetchone()
    if row:
        delete_location(lid, row[0], "SUB_BLOCK")

# ==========================================
# 3. MERGE DUPLICATES (keep the one with lowest ID, remove others)
# ==========================================
print("\n=== MERGING DUPLICATES ===")
duplicate_groups = [
    # (keep_id, remove_ids, canonical_name)
    (3,   [103, 104],   "HITEC City"),         # HITEC City / Hitec City / Hitec city
    (34,  [59],         "Bengaluru Urban"),     # Bengaluru Urban (2 copies)
    (60,  [263],        "Bhoganahalli"),        # Bhoganahalli (2 copies)
    (71,  [264],        "Chikagubbi"),          # Chikagubbi (2 copies)
    (91,  [92],         "Gundlapochampally"),   # Gundlapochampally (2 copies)
    (133, [244],        "Kollur"),              # Kollur / kollur
    (134, [245],        "Kompally"),            # Kompally / kompally
    (115, [335],        "K R Puram"),           # K R Puram / KR Puram
    (142, [143],        "LB Nagar"),            # L.B Nagar / LB Nagar
    (146, [164, 246],   "Mokila"),              # MOKILA / Mokila / mokila
    (174, [175],        "Nallagandla"),         # Nallagandla (2 copies)
    (184, [185],        "Osman Nagar"),         # Osman Nagar / Osman nagar
    (200, [247],        "Quthbullapur"),        # Quthbullapur / quthbullapur
    (201, [381],        "Rajaji Nagar"),        # Rajaji Nagar / Rajajinagar
    (380, [383],        "Rajarajeshwari Nagar"),# Raja Rajeshwari Nagar / Rajarajeshwari Nagar
    (213, [214],        "Serilingampally"),      # Serilingampally (2 copies)
    (222, [248],        "Suchitra"),            # Suchitra / suchitra
    (224, [226],        "Tellapur"),            # TELLAPUR / Tellapur
    (270, [271],        "Akshaya Nagar"),       # Akshaya Nagar / Akshayanagar
]

for keep_id, remove_ids, canonical in duplicate_groups:
    # Update the kept location's name to canonical
    cur.execute("UPDATE locations SET name = %s WHERE id = %s", (canonical, keep_id))
    
    for rid in remove_ids:
        cur.execute("SELECT name FROM locations WHERE id = %s", (rid,))
        row = cur.fetchone()
        if row:
            delete_location(rid, row[0], f"DUPLICATE of ID:{keep_id} '{canonical}'")

conn.commit()

# ==========================================
# 4. VERIFY FINAL STATE
# ==========================================
cur.execute("SELECT COUNT(*) FROM locations")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM location_insights")
ins = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM location_infrastructure")
infra = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM location_costs")
costs = cur.fetchone()[0]

print(f"\n{'='*55}")
print(f"  Removed admin zones:   {len(admin_zone_ids)}")
print(f"  Removed non-locations: {len(non_location_ids)}")
print(f"  Merged duplicate sets: {len(duplicate_groups)}")
print(f"  Locations remaining:   {total}")
print(f"  Insights:              {ins}")
print(f"  Infrastructure:        {infra}")
print(f"  Costs:                 {costs}")
print(f"{'='*55}")

cur.close()
conn.close()
