"""Quick check of Hyderabad locations boundaries"""
import psycopg2

conn = psycopg2.connect(
    host='localhost', user='postgres', 
    password='post@123', dbname='real_estate_intelligence'
)
cur = conn.cursor()

cur.execute("""
    SELECT id, name, 
           boundary IS NOT NULL as has_boundary,
           ST_Y(geom) as lat, ST_X(geom) as lng
    FROM locations 
    ORDER BY name
""")
rows = cur.fetchall()

print("\n" + "="*60)
print("📍 YOUR HYDERABAD LOCATIONS")
print("="*60)
print(f"{'ID':>3} | {'Location':<25} | {'Boundary':^10} | Coordinates")
print("-"*60)

for r in rows:
    boundary_status = "✓ Yes" if r[2] else "✗ No"
    coords = f"{r[3]:.4f}, {r[4]:.4f}" if r[3] and r[4] else "None"
    print(f"{r[0]:>3} | {r[1]:<25} | {boundary_status:^10} | {coords}")

# Count summary
cur.execute("SELECT COUNT(*) FROM locations")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM locations WHERE boundary IS NOT NULL")
with_boundary = cur.fetchone()[0]

print("-"*60)
print(f"Total: {total} locations | With boundary: {with_boundary}")
print("="*60)

cur.close()
conn.close()
