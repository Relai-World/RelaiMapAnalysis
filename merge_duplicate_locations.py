"""
Merge Duplicate Locations Properly
Updates all foreign key references before deleting duplicates
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

print("\n" + "="*80)
print("🔀 MERGING DUPLICATE LOCATIONS")
print("="*80)

# Find all duplicates
cur.execute("""
    SELECT name, array_agg(id ORDER BY id) as ids
    FROM locations
    WHERE city = 'Hyderabad'
    GROUP BY name
    HAVING COUNT(*) > 1
    ORDER BY name
""")

duplicates = cur.fetchall()

print(f"\nFound {len(duplicates)} locations with duplicates\n")

for name, ids in duplicates:
    keep_id = ids[0]  # Keep the first ID
    merge_ids = ids[1:]  # Merge these into the first
    
    print(f"📍 '{name}':")
    print(f"   Keeping ID: {keep_id}")
    print(f"   Merging IDs: {merge_ids}")
    
    # Update all foreign key references
    for merge_id in merge_ids:
        # Update location_infrastructure
        try:
            cur.execute(
                "UPDATE location_infrastructure SET location_id = %s WHERE location_id = %s",
                (keep_id, merge_id)
            )
            if cur.rowcount > 0:
                print(f"      ✅ Updated {cur.rowcount} location_infrastructure records")
        except Exception as e:
            print(f"      ⚠️  location_infrastructure: {e}")
        
        # Update location_costs
        try:
            cur.execute(
                "UPDATE location_costs SET location_id = %s WHERE location_id = %s",
                (keep_id, merge_id)
            )
            if cur.rowcount > 0:
                print(f"      ✅ Updated {cur.rowcount} location_costs records")
        except Exception as e:
            print(f"      ⚠️  location_costs: {e}")
        
        # Update location_insights
        try:
            cur.execute(
                "UPDATE location_insights SET location_id = %s WHERE location_id = %s",
                (keep_id, merge_id)
            )
            if cur.rowcount > 0:
                print(f"      ✅ Updated {cur.rowcount} location_insights records")
        except Exception as e:
            print(f"      ⚠️  location_insights: {e}")
        
        # Update price_trends
        try:
            cur.execute(
                "UPDATE price_trends SET location_id = %s WHERE location_id = %s",
                (keep_id, merge_id)
            )
            if cur.rowcount > 0:
                print(f"      ✅ Updated {cur.rowcount} price_trends records")
        except Exception as e:
            print(f"      ⚠️  price_trends: {e}")
        
        # Update news_balanced_corpus
        try:
            cur.execute(
                "UPDATE news_balanced_corpus SET location_id = %s WHERE location_id = %s",
                (keep_id, merge_id)
            )
            if cur.rowcount > 0:
                print(f"      ✅ Updated {cur.rowcount} news_balanced_corpus records")
        except Exception as e:
            print(f"      ⚠️  news_balanced_corpus: {e}")
        
        # Update raw_scraped_data
        try:
            cur.execute(
                "UPDATE raw_scraped_data SET location_id = %s WHERE location_id = %s",
                (keep_id, merge_id)
            )
            if cur.rowcount > 0:
                print(f"      ✅ Updated {cur.rowcount} raw_scraped_data records")
        except Exception as e:
            print(f"      ⚠️  raw_scraped_data: {e}")
        
        # Now delete the duplicate
        try:
            cur.execute("DELETE FROM locations WHERE id = %s", (merge_id,))
            print(f"      🗑️  Deleted duplicate ID {merge_id}")
        except Exception as e:
            print(f"      ❌ Error deleting: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    print()

# Also delete "Hyderabad Average" if it exists
print("🗑️  Removing invalid location 'Hyderabad Average'...")
try:
    # First get its ID
    cur.execute("SELECT id FROM locations WHERE name = 'Hyderabad Average' AND city = 'Hyderabad'")
    result = cur.fetchone()
    
    if result:
        invalid_id = result[0]
        
        # Update all references to NULL or delete them
        cur.execute("DELETE FROM location_infrastructure WHERE location_id = %s", (invalid_id,))
        cur.execute("DELETE FROM location_costs WHERE location_id = %s", (invalid_id,))
        cur.execute("DELETE FROM location_insights WHERE location_id = %s", (invalid_id,))
        cur.execute("DELETE FROM price_trends WHERE location_id = %s", (invalid_id,))
        cur.execute("DELETE FROM news_balanced_corpus WHERE location_id = %s", (invalid_id,))
        cur.execute("DELETE FROM raw_scraped_data WHERE location_id = %s", (invalid_id,))
        
        # Now delete the location
        cur.execute("DELETE FROM locations WHERE id = %s", (invalid_id,))
        print(f"   ✅ Deleted 'Hyderabad Average' and all its references")
        conn.commit()
except Exception as e:
    print(f"   ⚠️  {e}")
    conn.rollback()

# Final count
print("\n" + "="*80)
print("📊 FINAL RESULTS")
print("="*80)

cur.execute("SELECT COUNT(*) FROM locations WHERE city = 'Hyderabad'")
final_count = cur.fetchone()[0]

print(f"\n✅ Total unique locations: {final_count}")

# Check for remaining duplicates
cur.execute("""
    SELECT name, COUNT(*) as count
    FROM locations
    WHERE city = 'Hyderabad'
    GROUP BY name
    HAVING COUNT(*) > 1
""")

remaining_dupes = cur.fetchall()

if remaining_dupes:
    print(f"\n⚠️  Remaining duplicates: {len(remaining_dupes)}")
    for name, count in remaining_dupes:
        print(f"   - {name}: {count} entries")
else:
    print("\n✅ No duplicates remaining!")

print("\n" + "="*80)

cur.close()
conn.close()
