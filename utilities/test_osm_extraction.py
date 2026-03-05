import psycopg2
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Test with just one location
TEST_LOCATION = 'Gachibowli'

# Key amenities to test
TEST_AMENITIES = {
    'hospitals': 'amenity=hospital',
    'schools': 'amenity=school',
    'malls': 'shop=mall',
    'restaurants': 'amenity=restaurant',
    'metro_stations': 'railway=station',
    'banks': 'amenity=bank',
    'atms': 'amenity=atm',
    'parks': 'leisure=park',
    'gyms': 'leisure=fitness_centre',
    'cafes': 'amenity=cafe'
}

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def safe_count(lat, lng, osm_tag, radius=2000):
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius},{lat},{lng})[{osm_tag}];
      way(around:{radius},{lat},{lng})[{osm_tag}];
    );
    out count;
    """
    
    try:
        r = requests.post(OVERPASS_URL, data=query, timeout=30)
        if r.status_code != 200:
            return 0
        data = r.json()
        return len(data.get("elements", []))
    except Exception as e:
        print(f"  Error: {e}")
        return 0

print("=" * 80)
print(f"🧪 QUICK TEST: Extracting Amenities for {TEST_LOCATION}")
print("=" * 80)

conn = get_db_connection()
cur = conn.cursor()

# Get coordinates
cur.execute("""
    SELECT id, name, ST_Y(geom) AS latitude, ST_X(geom) AS longitude
    FROM locations
    WHERE name = %s
""", (TEST_LOCATION,))

result = cur.fetchone()

if not result:
    print(f"❌ Location '{TEST_LOCATION}' not found in database!")
    exit(1)

loc_id, name, lat, lng = result

print(f"\n📍 Location: {name}")
print(f"   Coordinates: {lat:.6f}, {lng:.6f}")
print(f"   Searching within 2km radius...\n")

print(f"{'Amenity':<25} {'Count':<10}")
print("-" * 80)

results = {}
for amenity_name, osm_tag in TEST_AMENITIES.items():
    print(f"Fetching {amenity_name}...", end=" ", flush=True)
    count = safe_count(lat, lng, osm_tag)
    results[amenity_name] = count
    print(f"{count}")
    time.sleep(1)  # Be polite

cur.close()
conn.close()

print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)

total = sum(results.values())
print(f"\nTotal amenities found: {total}\n")

print(f"{'Amenity Type':<25} {'Count':<10}")
print("-" * 80)
for amenity, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"{amenity.replace('_', ' ').title():<25} {count:<10}")

print("\n✅ Test complete!")
print("\nTo extract for all 7 locations, run: python extract_osm_amenities.py")
