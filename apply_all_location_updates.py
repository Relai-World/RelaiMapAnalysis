"""
apply_all_location_updates.py
──────────────────────────────
Applies ALL verified location updates from Google Places API
- Updates both Hyderabad AND Bengaluru locations
- Creates comprehensive backup before changes
- Shows progress and final summary
"""
import sys, os, time, json, psycopg2
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# ═══════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════
VERIFICATION_REPORT = "location_verification_dryrun_20260312_113058.json"
BACKUP_SQL = f"locations_full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

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

def create_backup():
    """Create SQL backup of current location data"""
    print("\n📦 CREATING DATABASE BACKUP...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch all current locations
    cur.execute("""
        SELECT id, name, ST_Y(geom) as lat, ST_X(geom) as lng 
        FROM locations 
        WHERE geom IS NOT NULL
        ORDER BY id
    """)
    
    locations = cur.fetchall()
    
    # Write backup SQL
    with open(BACKUP_SQL, 'w', encoding='utf-8') as f:
        f.write(f"-- Full Location Backup\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write(f"-- Total locations: {len(locations)}\n\n")
        
        for loc_id, name, lat, lng in locations:
            f.write(f"-- ID: {loc_id} - {name}\n")
            f.write(f"UPDATE locations SET geom = ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326) WHERE id = {loc_id};\n\n")
    
    cur.close()
    conn.close()
    
    print(f"✅ Backup saved to: {BACKUP_SQL}")
    print(f"   Contains {len(locations)} location records\n")

def apply_updates():
    """Apply all verified updates to database"""
    print("\n" + "="*80)
    print("🚀 APPLYING ALL LOCATION UPDATES")
    print("="*80)
    
    # Load verification report
    if not os.path.exists(VERIFICATION_REPORT):
        print(f"\n❌ Verification report not found: {VERIFICATION_REPORT}")
        print("   Please run verify_and_fix_all_locations.py first!")
        return
    
    print(f"\n📂 Loading: {VERIFICATION_REPORT}")
    with open(VERIFICATION_REPORT, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data['verification_results']
    
    # Filter updates to apply (both Hyderabad and Bengaluru)
    updates_to_apply = [
        r for r in results 
        if r['action'] in ['UPDATE_MINOR', 'UPDATE_MAJOR']
    ]
    
    review_items = [r for r in results if r['action'] == 'REVIEW_REQUIRED']
    
    print(f"\n📊 Update Summary:")
    print(f"   • Minor updates: {len([r for r in updates_to_apply if r['action'] == 'UPDATE_MINOR'])}")
    print(f"   • Major updates: {len([r for r in updates_to_apply if r['action'] == 'UPDATE_MAJOR'])}")
    print(f"   • Review required (skipped): {len(review_items)}")
    print(f"   • Total to apply: {len(updates_to_apply)}")
    
    if not updates_to_apply:
        print("\n✅ No updates to apply!")
        return
    
    # Safety confirmation
    print("\n⚠️  ABOUT TO UPDATE DATABASE")
    print(f"   This will modify {len(updates_to_apply)} location records.")
    print(f"   Backup will be saved to: {BACKUP_SQL}")
    confirm = input("\nProceed with updates? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("\n❌ Update cancelled by user.")
        return
    
    # Create backup first
    create_backup()
    
    # Apply updates
    conn = get_db_connection()
    cur = conn.cursor()
    
    applied = 0
    errors = 0
    hyd_count = 0
    blr_count = 0
    
    print("\n" + "="*80)
    print("🔧 UPDATING LOCATIONS...")
    print("="*80)
    
    try:
        for r in updates_to_apply:
            try:
                # Determine city
                city = r.get('city', 'Hyderabad') or 'Hyderabad'
                is_hyd = 'Hyderabad' in city
                
                # Update the geometry
                cur.execute("""
                    UPDATE locations
                    SET geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    WHERE id = %s
                """, (r["new_lng"], r["new_lat"], r["id"]))
                
                applied += 1
                if is_hyd:
                    hyd_count += 1
                else:
                    blr_count += 1
                
                status_icon = "✅" if is_hyd else "🏢"
                print(f"   {status_icon} {r['name']:35s} (ID: {r['id']:3d}) → Moved {r['distance_km']:.3f}km")
                
            except Exception as e:
                errors += 1
                print(f"   ❌ {r['name']} (ID: {r['id']}) - Error: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        
        print("\n" + "="*80)
        print("✅ UPDATE COMPLETE!")
        print("="*80)
        print(f"\n📈 Results:")
        print(f"   ✓ Successfully updated: {applied} locations")
        print(f"   ├─ Hyderabad locations: {hyd_count}")
        print(f"   └─ Bengaluru locations: {blr_count}")
        print(f"   ❌ Errors: {errors}")
        
        if review_items:
            print(f"\n⚠️  SKIPPED (Review Required): {len(review_items)} locations")
            print(f"   These need manual verification on Google Maps")
            print(f"   Top 5 largest moves:")
            sorted_reviews = sorted(review_items, key=lambda x: x['distance_km'], reverse=True)[:5]
            for item in sorted_reviews:
                print(f"      • {item['name']}: {item['distance_km']:.2f}km")
        
        print("\n💾 Backup file:")
        print(f"   {BACKUP_SQL}")
        print(f"   Use this to rollback if needed:\n")
        print(f"   psql -U postgres -d real_estate_intelligence -f {BACKUP_SQL}")
        
        print("\n" + "="*80)
        print("🎉 ALL DONE!")
        print("="*80)
        print("\n✅ Next Steps:")
        print("   1. Refresh your frontend map")
        print("   2. Check a few locations to verify accuracy")
        print("   3. Test property markers are now in correct positions")
        print("\n   Recommended test locations:")
        print("      • Appa Junction (was 8.8km off)")
        print("      • Ashok Nagar (was 10.8km off)")
        print("      • Financial District (was 1.9km off)")
        print("      • Whitefield, Electronic City (Bengaluru areas)")
        print("="*80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("Database rolled back to previous state.")
        import traceback
        traceback.print_exc()
    
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    try:
        apply_updates()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
