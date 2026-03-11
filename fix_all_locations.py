"""
Fix All Location Spellings and Merge Duplicates
Based on user-provided correct spellings
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Correct spellings mapping (incorrect -> correct)
CORRECTIONS = {
    "Alkapur Main Road": "Alkapur",
    "Budwel": "Budvel",
    "Damaragidda": "Damaragidda",  # Keep as is
    "Dollar Hill": "Dollar Hills",
    "Ghatkesar": "Ghatkesar",
    "Hayathnagar": "Hayathnagar",
    "Kowkur": "Kowkoor",
    "Lakdikapool": "Lakdikapul",
    "Mallapur": "Mallapur",
    "Shamshabad": "Shamshabad",
    "Toroor": "Tooroor",
    "Turkapally": "Turkapally",
    "Turkayamjal": "Turkayamjal",
}

# Locations to delete (invalid entries)
DELETE_LOCATIONS = [
    "Hyderabad Average"
]

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

print("\n" + "="*80)
print("🔧 FIXING ALL LOCATIONS")
print("="*80)

# Step 1: Apply spelling corrections
print("\n📝 Applying spelling corrections...")
for incorrect, correct in CORRECTIONS.items():
    try:
        cur.execute(
            "UPDATE locations SET name = %s WHERE name = %s AND city = 'Hyderabad'",
            (correct, incorrect)
        )
        if cur.rowcount > 0:
            print(f"   ✅ '{incorrect}' → '{correct}' ({cur.rowcount} records)")
    except Exception as e:
        print(f"   ❌ Error updating '{incorrect}': {e}")
        conn.rollback()

conn.commit()

# Step 2: Merge duplicates
print("\n🔀 Merging duplicates...")

# Get all duplicates
cur.execute("""
    SELECT name, COUNT(*) as count, array_agg(id) as ids
    FROM locations
    WHERE city = 'Hyderabad'
    GROUP BY name
    HAVING COUNT(*) > 1
    ORDER BY name
""")

duplicates = cur.fetchall()

for name, count, ids in duplicates:
    print(f"\n   📍 '{name}' has {count} duplicates (IDs: {ids})")
    
    # Keep the first ID, delete the rest
    keep_id = ids[0]
    delete_ids = ids[1:]
    
    for delete_id in delete_ids:
        try:
            cur.execute("DELETE FROM locations WHERE id = %s", (delete_id,))
            print(f"      🗑️  Deleted duplicate ID {delete_id}")
        except Exception as e:
            print(f"      ❌ Error deleting ID {delete_id}: {e}")
            conn.rollback()

conn.commit()

# Step 3: Delete invalid locations
print("\n🗑️  Deleting invalid locations...")
for location in DELETE_LOCATIONS:
    try:
        cur.execute(
            "DELETE FROM locations WHERE name = %s AND city = 'Hyderabad'",
            (location,)
        )
        if cur.rowcount > 0:
            print(f"   ✅ Deleted '{location}' ({cur.rowcount} records)")
    except Exception as e:
        print(f"   ❌ Error deleting '{location}': {e}")
        conn.rollback()

conn.commit()

# Step 4: Final count
print("\n" + "="*80)
print("📊 FINAL RESULTS")
print("="*80)

cur.execute("SELECT COUNT(*) FROM locations WHERE city = 'Hyderabad'")
final_count = cur.fetchone()[0]

print(f"\n✅ Total unique locations: {final_count}")

# Show all final locations
cur.execute("""
    SELECT name
    FROM locations
    WHERE city = 'Hyderabad'
    ORDER BY name
""")

locations = [row[0] for row in cur.fetchall()]

print(f"\n📍 All locations ({len(locations)}):\n")
for idx, name in enumerate(locations, 1):
    print(f"{idx:3d}. {name}")

print("\n" + "="*80)

cur.close()
conn.close()

print("\n✅ All corrections applied successfully!")
