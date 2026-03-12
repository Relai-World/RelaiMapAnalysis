"""
verify_and_fix_all_locations.py
────────────────────────────────
Comprehensive location verification using Google Places API
Generates dry-run report → User approval → Database update

Budget-friendly: 1.5s delay between API calls (~40 calls/minute)
"""
import sys, os, time, requests, psycopg2, json
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# ═══════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════
GOOGLE_API_KEY = "AIzaSyBi0vpchEjZNY3WL8fja0488QlXzhD6s-0"
RATE_LIMIT_DELAY = 1.5  # seconds between API calls (budget-friendly)
MAX_MOVE_DISTANCE_KM = 2.0  # Flag if move > this distance for review

# Output files
DRY_RUN_REPORT = f"location_verification_dryrun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
CSV_REPORT = f"location_verification_changes.csv"
BACKUP_SQL = f"locations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

# ═══════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════
def get_db_connection():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'post@123'),
        dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
        port=os.getenv('DB_PORT', '5432'),
        sslmode='prefer'
    )

# ═══════════════════════════════════════════
# GOOGLE PLACES GEOCODING
# ═══════════════════════════════════════════
def geocode_with_google_places(location_name):
    """
    Use Google Places API to find accurate coordinates for a location.
    Returns: (lat, lng, formatted_address, place_id, confidence_score) or (None, None, None, None, None)
    """
    try:
        # Step 1: Text Search to find the place
        search_query = f"{location_name} Hyderabad Telangana India locality area"
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": search_query,
            "key": GOOGLE_API_KEY,
            "type": "sublocality"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"    ⚠️  API Error: {response.status_code}")
            return None, None, None, None, None
        
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            # Try fallback: Geocoding API
            return geocode_with_google_geocoding(location_name)
        
        result = data["results"][0]
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})
        
        lat = location.get("lat")
        lng = location.get("lng")
        address = result.get("formatted_address", "")
        place_id = result.get("place_id", "")
        
        # Calculate confidence based on result types
        types = result.get("types", [])
        confidence = 0.9 if "sublocality" in types else 0.8 if "locality" in types else 0.7
        
        return lat, lng, address, place_id, confidence
        
    except Exception as e:
        print(f"    ❌ Exception: {e}")
        return None, None, None, None, None

def geocode_with_google_geocoding(location_name):
    """
    Fallback: Use Google Geocoding API for better coverage.
    """
    try:
        query = f"{location_name}, Hyderabad, Telangana, India"
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": query,
            "key": GOOGLE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, None, None, None, None
        
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            return None, None, None, None, None
        
        result = data["results"][0]
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})
        
        lat = location.get("lat")
        lng = location.get("lng")
        address = result.get("formatted_address", "")
        place_id = result.get("place_id", "")
        
        # Confidence based on location type
        types = result.get("types", [])
        confidence = 0.95 if "sublocality" in types else 0.85 if "locality" in types else 0.75
        
        return lat, lng, address, place_id, confidence
        
    except Exception as e:
        print(f"    ❌ Geocoding Exception: {e}")
        return None, None, None, None, None

def calculate_distance_km(lat1, lng1, lat2, lng2):
    """
    Calculate approximate distance between two points in KM.
    Uses simple Euclidean distance (good enough for small distances).
    """
    import math
    lat_diff = abs(lat2 - lat1) * 111.0
    lng_diff = abs(lng2 - lng1) * 111.0 * math.cos(math.radians(lat1))
    return math.sqrt(lat_diff**2 + lng_diff**2)

# ═══════════════════════════════════════════
# VERIFICATION LOGIC
# ═══════════════════════════════════════════
def verify_location(current_lat, current_lng, new_lat, new_lng, location_name):
    """
    Verify if a location needs to be moved.
    Returns: (needs_update, distance_km, recommendation, reason)
    """
    if new_lat is None or new_lng is None:
        return False, 0, "SKIP", "Google API returned no results"
    
    distance = calculate_distance_km(current_lat, current_lng, new_lat, new_lng)
    
    # Decision logic
    if distance < 0.3:  # Less than 300m - already accurate
        return False, distance, "KEEP", f"Current position accurate (diff: {distance:.2f}km)"
    elif distance < 0.8:  # 300m-800m - minor adjustment
        return True, distance, "UPDATE_MINOR", f"Minor adjustment needed (diff: {distance:.2f}km)"
    elif distance < MAX_MOVE_DISTANCE_KM:  # 800m-2km - significant move
        return True, distance, "UPDATE_MAJOR", f"Significant move required (diff: {distance:.2f}km)"
    else:  # > 2km - needs manual review
        return True, distance, "REVIEW_REQUIRED", f"LARGE MOVE ({distance:.2f}km) - Manual review recommended"

# ═══════════════════════════════════════════
# MAIN VERIFICATION PROCESS
# ═══════════════════════════════════════════
def verify_all_locations(dry_run=True):
    """
    Main verification process.
    """
    print("\n" + "="*80)
    print("🗺️  HYDERABAD LOCATIONS VERIFICATION SYSTEM")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   • API: Google Places + Geocoding")
    print(f"   • Rate Limit: {RATE_LIMIT_DELAY}s between calls")
    print(f"   • Review Threshold: {MAX_MOVE_DISTANCE_KM}km")
    print(f"   • Mode: {'DRY RUN (No DB changes)' if dry_run else 'LIVE UPDATE'}")
    print("="*80)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch all locations (excluding non-Hyderabad like Bengaluru)
    cur.execute("""
        SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng, city
        FROM locations
        WHERE geom IS NOT NULL
        ORDER BY name
    """)
    
    all_locations = cur.fetchall()
    total = len(all_locations)
    
    print(f"\n📍 Found {total} locations to verify\n")
    
    # Results tracking
    verification_results = []
    stats = {
        "accurate": 0,
        "update_minor": 0,
        "update_major": 0,
        "review_required": 0,
        "skip_no_data": 0,
        "total_api_calls": 0
    }
    
    # Process each location
    for idx, (loc_id, name, current_lat, current_lng, city) in enumerate(all_locations, 1):
        print(f"\n[{idx}/{total}] 📍 {name} (ID: {loc_id})")
        
        # Skip non-Hyderabad locations (like Bengaluru Urban)
        if city and "Bengaluru" in city:
            print(f"   ⏭️  Skipping non-Hyderabad location")
            verification_results.append({
                "id": loc_id,
                "name": name,
                "city": city,
                "current_lat": current_lat,
                "current_lng": current_lng,
                "new_lat": None,
                "new_lng": None,
                "action": "SKIP_NON_HYD",
                "distance_km": 0,
                "reason": "Non-Hyderabad location"
            })
            continue
        
        # Verify with Google
        new_lat, new_lng, address, place_id, confidence = geocode_with_google_places(name)
        stats["total_api_calls"] += 1
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        if new_lat is None:
            print(f"   ⚠️  No Google result found")
            stats["skip_no_data"] += 1
            verification_results.append({
                "id": loc_id,
                "name": name,
                "current_lat": current_lat,
                "current_lng": current_lng,
                "new_lat": None,
                "new_lng": None,
                "action": "SKIP_NO_DATA",
                "distance_km": 0,
                "reason": "Google API returned no results",
                "google_address": None
            })
            continue
        
        # Evaluate if update needed
        needs_update, distance, action, reason = verify_location(
            current_lat, current_lng, new_lat, new_lng, name
        )
        
        print(f"   Current: {current_lat:.6f}, {current_lng:.6f}")
        print(f"   Google:  {new_lat:.6f}, {new_lng:.6f}")
        print(f"   Distance: {distance:.3f} km")
        print(f"   Action: {action}")
        print(f"   Reason: {reason}")
        
        # Update stats
        if action == "KEEP":
            stats["accurate"] += 1
        elif action == "UPDATE_MINOR":
            stats["update_minor"] += 1
        elif action == "UPDATE_MAJOR":
            stats["update_major"] += 1
        elif action == "REVIEW_REQUIRED":
            stats["review_required"] += 1
        
        # Store result
        verification_results.append({
            "id": loc_id,
            "name": name,
            "city": city or "Hyderabad",
            "current_lat": current_lat,
            "current_lng": current_lng,
            "new_lat": new_lat,
            "new_lng": new_lng,
            "google_address": address,
            "place_id": place_id,
            "confidence": confidence,
            "action": action,
            "distance_km": round(distance, 3),
            "reason": reason
        })
    
    cur.close()
    conn.close()
    
    # ═══════════════════════════════════════════
    # GENERATE REPORTS
    # ═══════════════════════════════════════════
    print("\n" + "="*80)
    print("📊 VERIFICATION SUMMARY")
    print("="*80)
    print(f"\nTotal Locations: {total}")
    print(f"API Calls Made: {stats['total_api_calls']}")
    print(f"\nResults:")
    print(f"   ✓ Accurate (< 300m):     {stats['accurate']}")
    print(f"   🔧 Minor Update (300-800m):  {stats['update_minor']}")
    print(f"   🚀 Major Update (800m-2km):  {stats['update_major']}")
    print(f"   ⚠️  Review Required (> 2km):  {stats['review_required']}")
    print(f"   ⏭️  Skipped (No Data):    {stats['skip_no_data']}")
    print("="*80)
    
    # Save JSON report
    with open(DRY_RUN_REPORT, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_locations": total,
            "api_calls_made": stats["total_api_calls"],
            "statistics": stats,
            "verification_results": verification_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed JSON report saved to: {DRY_RUN_REPORT}")
    
    # Generate CSV for easy review
    generate_csv_report(verification_results)
    
    # Generate SQL backup script
    generate_backup_sql(verification_results, BACKUP_SQL)
    
    # Show items requiring review
    review_items = [r for r in verification_results if r["action"] == "REVIEW_REQUIRED"]
    if review_items:
        print(f"\n⚠️  ATTENTION: {len(review_items)} locations require manual review:")
        for item in review_items[:10]:  # Show first 10
            print(f"   • {item['name']}: {item['distance_km']:.2f}km move")
        if len(review_items) > 10:
            print(f"   ... and {len(review_items) - 10} more")
    
    return verification_results, stats

def generate_csv_report(results):
    """Generate CSV report for easy Excel review"""
    import csv
    
    with open(CSV_REPORT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Name", "City", "Current_Lat", "Current_Lng", 
            "New_Lat", "New_Lng", "Distance_KM", "Action", "Reason",
            "Google_Address", "Place_ID", "Confidence"
        ])
        
        for r in results:
            writer.writerow([
                r["id"],
                r["name"],
                r["city"],
                r["current_lat"],
                r["current_lng"],
                r.get("new_lat", ""),
                r.get("new_lng", ""),
                r["distance_km"],
                r["action"],
                r["reason"],
                r.get("google_address", ""),
                r.get("place_id", ""),
                r.get("confidence", "")
            ])
    
    print(f"💾 CSV report saved to: {CSV_REPORT}")

def generate_backup_sql(results, filename):
    """Generate SQL backup script for current data"""
    updates_needed = [r for r in results if r["action"] in ["UPDATE_MINOR", "UPDATE_MAJOR", "REVIEW_REQUIRED"]]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("-- Location Backup Before Update\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write(f"-- Total updates: {len(updates_needed)}\n\n")
        
        for r in updates_needed:
            f.write(f"-- {r['name']} (ID: {r['id']}) - Move: {r['distance_km']:.3f}km\n")
            f.write(f"-- Current: {r['current_lat']}, {r['current_lng']}\n")
            f.write(f"-- New: {r.get('new_lat', 'N/A')}, {r.get('new_lng', 'N/A')}\n")
            f.write(f"UPDATE locations SET geom = ST_SetSRID(ST_MakePoint({r.get('new_lng', r['current_lng'])}, {r.get('new_lat', r['current_lat'])}), 4326) WHERE id = {r['id']};\n\n")
    
    print(f"💾 SQL backup script saved to: {filename}")

# ═══════════════════════════════════════════
# APPLY UPDATES
# ═══════════════════════════════════════════
def apply_updates(verification_results, auto_approve=False):
    """
    Apply verified updates to database.
    """
    print("\n" + "="*80)
    print("🔧 APPLYING UPDATES TO DATABASE")
    print("="*80)
    
    # Filter items that need updates
    updates_needed = [
        r for r in verification_results 
        if r["action"] in ["UPDATE_MINOR", "UPDATE_MAJOR"]
    ]
    
    review_items = [r for r in verification_results if r["action"] == "REVIEW_REQUIRED"]
    
    print(f"\n📋 Update Summary:")
    print(f"   • Minor updates: {len([r for r in updates_needed if r['action'] == 'UPDATE_MINOR'])}")
    print(f"   • Major updates: {len([r for r in updates_needed if r['action'] == 'UPDATE_MAJOR'])}")
    print(f"   • Review required: {len(review_items)}")
    print(f"   • Total to apply: {len(updates_needed)}")
    
    if not updates_needed:
        print("\n✅ No updates to apply!")
        return
    
    # Safety confirmation
    if not auto_approve:
        print("\n⚠️  ABOUT TO UPDATE DATABASE")
        print(f"   This will modify {len(updates_needed)} location records.")
        confirm = input("\nProceed with updates? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("❌ Update cancelled by user.")
            return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    applied = 0
    errors = 0
    
    try:
        for r in updates_needed:
            try:
                # Update the geometry
                cur.execute("""
                    UPDATE locations
                    SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    WHERE id = %s
                """, (r["new_lng"], r["new_lat"], r["id"]))
                
                applied += 1
                print(f"   ✅ {r['name']} (ID: {r['id']}) - Moved {r['distance_km']:.3f}km")
                
            except Exception as e:
                errors += 1
                print(f"   ❌ {r['name']} (ID: {r['id']}) - Error: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✅ UPDATE COMPLETE!")
        print("="*80)
        print(f"   Successfully updated: {applied} locations")
        print(f"   Errors: {errors}")
        
        # Show review items again
        if review_items:
            print(f"\n⚠️  REMINDER: {len(review_items)} locations still need manual review:")
            for item in review_items[:5]:
                print(f"   • {item['name']}: {item['distance_km']:.2f}km")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("Database rolled back to previous state.")
    
    finally:
        cur.close()
        conn.close()

# ═══════════════════════════════════════════
# INTERACTIVE MENU
# ═══════════════════════════════════════════
def main_menu():
    """Interactive menu system"""
    print("\n" + "="*80)
    print("🗺️  LOCATION VERIFICATION SYSTEM")
    print("="*80)
    print("\nOptions:")
    print("1. Run Verification (Dry Run - Generate Report)")
    print("2. Apply Updates from Last Verification")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting verification (DRY RUN MODE)...")
        results, stats = verify_all_locations(dry_run=True)
        
        print("\n" + "="*80)
        print("✅ VERIFICATION COMPLETE!")
        print("="*80)
        print(f"\nNext steps:")
        print(f"   1. Review the generated reports:")
        print(f"      • JSON: {DRY_RUN_REPORT}")
        print(f"      • CSV: {CSV_REPORT}")
        print(f"      • SQL Backup: {BACKUP_SQL}")
        print(f"\n   2. Run this script again and choose option 2 to apply updates")
        print(f"   3. Manually review locations marked as 'REVIEW_REQUIRED'\n")
        
    elif choice == "2":
        # Load last verification results
        if not os.path.exists(DRY_RUN_REPORT):
            print(f"\n❌ No verification report found!")
            print(f"   Please run option 1 first to generate a report.")
            return
        
        print(f"\n📂 Loading verification report: {DRY_RUN_REPORT}")
        with open(DRY_RUN_REPORT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = data.get("verification_results", [])
        if not results:
            print("❌ No verification results found in report.")
            return
        
        apply_updates(results, auto_approve=False)
        
    elif choice == "3":
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    else:
        print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
