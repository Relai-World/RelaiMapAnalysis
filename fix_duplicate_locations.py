"""
fix_duplicate_locations.py
──────────────────────────
Fixes 10 duplicate location entries in the `locations` table.
Uses Google Geocoding API first, falls back to Nominatim OSM.
For locations that both fail, uses manually verified correct coords.
"""
import sys, os, time, requests, psycopg2
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

GOOGLE_API_KEY = "AIzaSyBi0vpchEjZNY3WL8fja0488QlXzhD6s-0"

# Manually verified coords (from Google Maps) for fallback cases
MANUAL_COORDS = {
    "Appa Junction":  (17.4385133, 78.3647623, "Appa Junction, Hyderabad [manual]"),
    "Kollur":         (17.4695855, 78.2925823, "Kollur, Ranga Reddy, Telangana [manual]"),
    "Peerancheru":    (17.5280000, 78.2641269, "Peerancheru, Sangareddy, Telangana [manual]"),
    "Velimela":       (17.2780000, 78.3870000, "Velimela, Ranga Reddy, Telangana [manual]"),
}

# (name, [IDs], google_search_query)
DUPLICATES = [
    ("Appa Junction",  [41, 42],    "Appa Junction Hyderabad Telangana India"),
    ("Khajaguda",      [117, 128],  "Khajaguda Hyderabad Telangana India"),
    ("Kollur",         [133, 190],  "Kollur village Ranga Reddy Telangana India"),
    ("Madhapur",       [4, 94],     "Madhapur Hyderabad Telangana India"),
    ("Manchirevula",   [153, 261],  "Manchirevula Hyderabad Telangana India"),
    ("Patancheru",     [188, 189],  "Patancheru Hyderabad Telangana India"),
    ("Peerancheru",    [192, 193],  "Peerancheru Sangareddy Telangana India"),
    ("Puppalaguda",    [198, 199],  "Puppalaguda Hyderabad Telangana India"),
    ("Secunderabad",   [186, 211],  "Secunderabad Hyderabad Telangana India"),
    ("Velimela",       [236, 262],  "Velimela Ranga Reddy Telangana India"),
]

def geocode_google(query):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    try:
        resp = requests.get(url, params={"address": query, "key": GOOGLE_API_KEY}, timeout=8)
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            loc  = data["results"][0]["geometry"]["location"]
            addr = data["results"][0]["formatted_address"]
            return loc["lat"], loc["lng"], addr
    except Exception:
        pass
    return None, None, None

def geocode_nominatim(query):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "HydIntelligenceApp/1.0"}
    try:
        resp = requests.get(url, params={"q": query, "format": "json", "limit": 1,
                                         "countrycodes": "in"},
                            headers=headers, timeout=8)
        results = resp.json()
        if results:
            r = results[0]
            return float(r["lat"]), float(r["lon"]), r["display_name"]
    except Exception:
        pass
    return None, None, None

def geocode(name, query):
    """Try Google → Nominatim → manual fallback."""
    lat, lng, addr = geocode_google(query)
    if lat:
        return lat, lng, f"[Google] {addr}"
    time.sleep(0.3)
    lat, lng, addr = geocode_nominatim(query)
    if lat:
        return lat, lng, f"[Nominatim] {addr}"
    if name in MANUAL_COORDS:
        lat, lng, addr = MANUAL_COORDS[name]
        return lat, lng, addr
    return None, None, None

def connect():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'post@123'),
        dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
        port=os.getenv('DB_PORT', '5432'),
        sslmode='prefer'
    )

def main():
    conn = connect()
    cur  = conn.cursor()

    print("="*72)
    print("  GEOCODING PLAN — Google → Nominatim → Manual fallback")
    print("="*72)

    plan = []

    for name, ids, query in DUPLICATES:
        lat, lng, address = geocode(name, query)
        time.sleep(0.3)

        keep_id    = ids[0]
        delete_ids = ids[1:]

        if lat is None:
            print(f"\n  ❌ '{name}'  — ALL geocoders failed. SKIPPING.")
            continue

        # Show current coords in DB
        cur.execute("SELECT id, ST_AsText(geom) FROM locations WHERE id = ANY(%s)", (ids,))
        db_rows = {row[0]: row[1] for row in cur.fetchall()}

        print(f"\n  📍 '{name}'")
        print(f"     Resolved to: lat={lat:.7f}, lng={lng:.7f}")
        print(f"     Source:      {address[:100]}")
        for rid in ids:
            flag = "← KEEP + UPDATE" if rid == keep_id else "← DELETE"
            print(f"     DB ID={rid}: {db_rows.get(rid, 'N/A')}  {flag}")

        plan.append((name, keep_id, delete_ids, lat, lng))

    print(f"\n{'='*72}")
    print(f"  {len(plan)} locations resolved | {sum(len(d[2]) for d in plan)} duplicate rows to delete")
    print(f"{'='*72}")

    ans = input("\nApply all fixes to the database? [y/N]: ").strip().lower()
    if ans != 'y':
        print("Aborted — no changes made.")
        cur.close(); conn.close(); return

    # Tables that have a FK to locations.id
    FK_TABLES = [
        ("location_costs",          "location_id"),
        ("location_infrastructure", "location_id"),
        ("location_insights",       "location_id"),
        ("raw_scraped_data",        "location_id"),
    ]

    # ── Apply inside a single transaction ─────────────────────
    fixed = deleted = 0
    try:
        for name, keep_id, delete_ids, lat, lng in plan:
            # 1. Update geometry on keeper row
            cur.execute("""
                UPDATE locations
                SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                WHERE id = %s
            """, (lng, lat, keep_id))

            for del_id in delete_ids:
                # 2. Reassign all FK references from del_id → keep_id
                for tbl, col in FK_TABLES:
                    # Use savepoint so a unique-constraint failure doesn't kill the whole txn
                    cur.execute(f"SAVEPOINT sp_{tbl}")
                    try:
                        cur.execute(f"UPDATE {tbl} SET {col} = %s WHERE {col} = %s",
                                    (keep_id, del_id))
                        if cur.rowcount:
                            print(f"     ↳ Reassigned {cur.rowcount} row(s) in {tbl}: {del_id} → {keep_id}")
                        cur.execute(f"RELEASE SAVEPOINT sp_{tbl}")
                    except Exception:
                        # Keeper already has a row — the duplicate's data is redundant, just delete it
                        cur.execute(f"ROLLBACK TO SAVEPOINT sp_{tbl}")
                        cur.execute(f"RELEASE SAVEPOINT sp_{tbl}")
                        cur.execute(f"DELETE FROM {tbl} WHERE {col} = %s", (del_id,))
                        if cur.rowcount:
                            print(f"     ↳ Deleted {cur.rowcount} redundant row(s) from {tbl} (unique conflict on ID={del_id})")

                # 3. Now safe to delete
                cur.execute("DELETE FROM locations WHERE id = %s", (del_id,))
                deleted += 1
            fixed += 1
            print(f"  ✅  '{name}'  → ID={keep_id} updated to ({lat:.6f},{lng:.6f}), deleted {delete_ids}")

        conn.commit()
        print(f"\n✅  Done! {fixed} locations fixed, {deleted} duplicate rows removed.")

        cur.execute("SELECT COUNT(*) FROM locations WHERE city ILIKE '%Hyderabad%';")
        print(f"   Hyderabad locations now: {cur.fetchone()[0]}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌  Error: {e}\n    Rolled back — no changes made.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
