import psycopg2
import requests
import time
from tqdm import tqdm

# ===============================
# CONFIG
# ===============================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_db_connection():
    return psycopg2.connect(
        dbname="real_estate_intelligence",
        user="postgres",
        password="post@123",
        host="localhost",
        port=5432
    )

def safe_count(query: str) -> int:
    try:
        r = requests.post(
            OVERPASS_URL,
            data=query,
            timeout=25,
            headers={"Accept": "application/json", "User-Agent": "RealEstateBot/1.0"}
        )
        if r.status_code != 200:
            return 0
        data = r.json()
        return len(data.get("elements", []))
    except Exception:
        return 0

def run():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Create table if not exists
    print("🛠️  Ensuring infrastructure table exists...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS location_infrastructure (
            location_id INTEGER PRIMARY KEY REFERENCES locations(id),
            hospitals INTEGER DEFAULT 0,
            schools INTEGER DEFAULT 0,
            metro INTEGER DEFAULT 0,
            airports INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # 2. Get locations
    cur.execute("SELECT id, ST_Y(geom), ST_X(geom), name FROM locations")
    locations = cur.fetchall()
    print(f"🌍 Found {len(locations)} locations to process.")

    # 3. Process each location
    for loc_id, lat, lng, name in tqdm(locations):
        base_query = f"""
        [out:json][timeout:25];
        (
          node(around:3000,{lat},{lng})[{{0}}];
          way(around:3000,{lat},{lng})[{{0}}];
        );
        out body;
        """

        # Fetch counts (Slow part happens here, offline)
        hospitals = safe_count(base_query.format("amenity=hospital"))
        schools = safe_count(base_query.format("amenity=school"))
        metro = safe_count(base_query.format("railway=station"))
        airports = safe_count(base_query.format("aeroway=aerodrome"))

        # Upsert into DB
        cur.execute("""
            INSERT INTO location_infrastructure (location_id, hospitals, schools, metro, airports)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (location_id) 
            DO UPDATE SET
                hospitals = EXCLUDED.hospitals,
                schools = EXCLUDED.schools,
                metro = EXCLUDED.metro,
                airports = EXCLUDED.airports,
                last_updated = CURRENT_TIMESTAMP;
        """, (loc_id, hospitals, schools, metro, airports))
        
        conn.commit()
        time.sleep(1) # Be polite to Overpass API

    cur.close()
    conn.close()
    print("✅ Infrastructure data pre-fetched successfully.")

if __name__ == "__main__":
    run()