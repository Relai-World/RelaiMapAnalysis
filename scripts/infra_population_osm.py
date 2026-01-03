import psycopg2
import requests
import time

DB_CONFIG = {
    "dbname": "real_estate_intelligence",
    "user": "postgres",
    "password": "post@123",
    "host": "localhost",
    "port": 5432
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

RADIUS_METERS = 4000
SLEEP_SECONDS = 1.5   # avoid 429 / 504

OSM_QUERIES = {
    "hospitals_count": 'node["amenity"="hospital"]',
    "schools_count": 'node["amenity"="school"]',
    "metro_count": 'node["railway"="station"]',
    "airports_count": 'node["aeroway"="aerodrome"]'
}


def fetch_count(lat, lon, query):
    overpass_query = f"""
    [out:json][timeout:25];
    (
      {query}(around:{RADIUS_METERS},{lat},{lon});
    );
    out count;
    """

    r = requests.post(OVERPASS_URL, data=overpass_query, timeout=30)
    r.raise_for_status()
    data = r.json()

    return int(data["elements"][0]["tags"]["total"])


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # fetch all locations
    cur.execute("""
        SELECT id, ST_Y(geom) AS lat, ST_X(geom) AS lon
        FROM locations
        ORDER BY id;
    """)
    locations = cur.fetchall()

    print(f"\n📍 Processing {len(locations)} locations\n")

    for loc_id, lat, lon in locations:
        print(f"Location ID {loc_id}")

        results = {}
        for column, osm_query in OSM_QUERIES.items():
            try:
                count = fetch_count(lat, lon, osm_query)
                results[column] = count
                print(f"  {column}: {count}")
                time.sleep(SLEEP_SECONDS)
            except Exception as e:
                print(f"  ❌ {column} failed:", e)
                results[column] = 0

        # ✅ INSERT INTO CORRECT TABLE
        cur.execute("""
            INSERT INTO location_infra_counts
                (location_id, hospitals_count, schools_count, metro_count, airports_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (location_id)
            DO UPDATE SET
                hospitals_count = EXCLUDED.hospitals_count,
                schools_count = EXCLUDED.schools_count,
                metro_count = EXCLUDED.metro_count,
                airports_count = EXCLUDED.airports_count,
                last_updated = CURRENT_TIMESTAMP;
        """, (
            loc_id,
            results["hospitals_count"],
            results["schools_count"],
            results["metro_count"],
            results["airports_count"]
        ))

        conn.commit()
        print("  ✅ Saved\n")

    cur.close()
    conn.close()
    print("🎯 OSM infra population completed successfully.")


if __name__ == "__main__":
    main()
