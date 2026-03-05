import psycopg2
import requests
import time
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ===============================
# CONFIG
# ===============================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Your 7 locations
TARGET_LOCATIONS = [
    'Financial District',
    'Gachibowli',
    'HITEC City',
    'Kondapur',
    'Kukatpally',
    'Madhapur',
    'Nanakramguda'
]

# Comprehensive amenity types to extract
AMENITY_TYPES = {
    # Healthcare
    'hospitals': 'amenity=hospital',
    'clinics': 'amenity=clinic',
    'pharmacies': 'amenity=pharmacy',
    
    # Education
    'schools': 'amenity=school',
    'colleges': 'amenity=college',
    'universities': 'amenity=university',
    'kindergartens': 'amenity=kindergarten',
    
    # Shopping
    'malls': 'shop=mall',
    'supermarkets': 'shop=supermarket',
    'convenience_stores': 'shop=convenience',
    
    # Food & Dining
    'restaurants': 'amenity=restaurant',
    'cafes': 'amenity=cafe',
    'fast_food': 'amenity=fast_food',
    
    # Transportation
    'metro_stations': 'railway=station',
    'bus_stops': 'highway=bus_stop',
    'airports': 'aeroway=aerodrome',
    
    # Banking
    'banks': 'amenity=bank',
    'atms': 'amenity=atm',
    
    # Recreation
    'parks': 'leisure=park',
    'gyms': 'leisure=fitness_centre',
    'cinemas': 'amenity=cinema',
    'playgrounds': 'leisure=playground',
    
    # Religious
    'places_of_worship': 'amenity=place_of_worship',
    
    # Safety
    'police_stations': 'amenity=police',
    'fire_stations': 'amenity=fire_station',
    
    # Others
    'libraries': 'amenity=library',
    'community_centers': 'amenity=community_centre',
    'post_offices': 'amenity=post_office'
}

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def safe_count(lat, lng, osm_tag, radius=000):
    """Fetch count of amenities from OSM Overpass API"""
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius},{lat},{lng})[{osm_tag}];
      way(around:{radius},{lat},{lng})[{osm_tag}];
      relation(around:{radius},{lat},{lng})[{osm_tag}];
    );
    out count;
    """
    
    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "WestHyderabadIntel/1.0"
        }
        r = requests.post(OVERPASS_URL, data=query, timeout=30, headers=headers)
        
        if r.status_code != 200:
            return 0
        
        data = r.json()
        
        # Try to get count from response
        total = 0
        for el in data.get("elements", []):
            if "tags" in el and "total" in el["tags"]:
                total += int(el["tags"]["total"])
        
        # If no count tag, count elements
        if total == 0:
            total = len(data.get("elements", []))
        
        return total
    except Exception as e:
        print(f"  ⚠️  Error fetching {osm_tag}: {e}")
        return 0

def extract_amenities_for_locations():
    """Extract amenity counts for all 7 locations"""
    
    print("=" * 100)
    print("🗺️  EXTRACTING AMENITIES FROM OPENSTREETMAP")
    print("=" * 100)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get location coordinates
    print("\n📍 Fetching location coordinates from database...")
    cur.execute("""
        SELECT id, name, ST_Y(geom) AS latitude, ST_X(geom) AS longitude
        FROM locations
        WHERE name = ANY(%s)
        ORDER BY name
    """, (TARGET_LOCATIONS,))
    
    locations = cur.fetchall()
    
    if len(locations) == 0:
        print("❌ No locations found in database!")
        return
    
    print(f"✓ Found {len(locations)} locations\n")
    
    results = {}
    
    for loc_id, name, lat, lng in locations:
        print(f"\n{'='*100}")
        print(f"📍 {name}")
        print(f"{'='*100}")
        print(f"Coordinates: {lat:.4f}, {lng:.4f}")
        print(f"Searching within 2km radius...")
        print()
        
        amenity_counts = {}
        
        # Fetch each amenity type
        for amenity_name, osm_tag in tqdm(AMENITY_TYPES.items(), desc=f"Fetching {name}"):
            count = safe_count(lat, lng, osm_tag)
            amenity_counts[amenity_name] = count
            time.sleep(1)  # Be polite to OSM API
        
        results[name] = {
            'location_id': loc_id,
            'latitude': lat,
            'longitude': lng,
            'amenities': amenity_counts
        }
        
        # Print summary
        print(f"\n📊 Summary for {name}:")
        print("-" * 100)
        total_amenities = sum(amenity_counts.values())
        print(f"Total amenities found: {total_amenities}")
        print(f"\nTop amenities:")
        sorted_amenities = sorted(amenity_counts.items(), key=lambda x: x[1], reverse=True)
        for amenity, count in sorted_amenities[:10]:
            if count > 0:
                print(f"  • {amenity.replace('_', ' ').title():<30} {count:>4}")
    
    cur.close()
    conn.close()
    
    # Save results
    print("\n" + "=" * 100)
    print("💾 SAVING RESULTS")
    print("=" * 100)
    
    # Save as text report
    with open("OSM_AMENITIES_REPORT.txt", "w", encoding="utf-8") as f:
        f.write("=" * 100 + "\n")
        f.write("OPENSTREETMAP AMENITIES ANALYSIS - WEST HYDERABAD\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Search Radius: 2km from each location center\n")
        f.write(f"Data Source: OpenStreetMap via Overpass API\n")
        f.write(f"Total Locations: {len(results)}\n\n")
        
        for location, data in results.items():
            f.write(f"\n{'='*100}\n")
            f.write(f"{location.upper()}\n")
            f.write(f"{'='*100}\n")
            f.write(f"Location ID: {data['location_id']}\n")
            f.write(f"Coordinates: {data['latitude']:.6f}, {data['longitude']:.6f}\n\n")
            
            amenities = data['amenities']
            total = sum(amenities.values())
            f.write(f"Total Amenities: {total}\n\n")
            
            f.write(f"{'Amenity Type':<35} {'Count':<10}\n")
            f.write("-" * 100 + "\n")
            
            for amenity, count in sorted(amenities.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{amenity.replace('_', ' ').title():<35} {count:<10}\n")
    
    # Save as JSON
    import json
    with open("OSM_AMENITIES_DATA.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("✓ Saved to OSM_AMENITIES_REPORT.txt")
    print("✓ Saved to OSM_AMENITIES_DATA.json")
    
    # Print final summary
    print("\n" + "=" * 100)
    print("📊 FINAL SUMMARY")
    print("=" * 100)
    print(f"\n{'Location':<25} {'Total Amenities':<20} {'Top Amenity'}")
    print("-" * 100)
    
    for location, data in results.items():
        total = sum(data['amenities'].values())
        top_amenity = max(data['amenities'].items(), key=lambda x: x[1])
        top_name = top_amenity[0].replace('_', ' ').title()
        top_count = top_amenity[1]
        print(f"{location:<25} {total:<20} {top_name} ({top_count})")
    
    print("\n✅ EXTRACTION COMPLETE!")
    print("\nNote: This data can be stored in your database for faster access.")

if __name__ == "__main__":
    extract_amenities_for_locations()
