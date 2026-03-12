import psycopg2
import os
import sys
from dotenv import load_dotenv

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'post@123'),
    dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
    port=os.getenv('DB_PORT', '5432'),
    sslmode='require' if os.getenv('DB_HOST', 'localhost') != 'localhost' else 'prefer'
)

cur = conn.cursor()

# Total rows
cur.execute("SELECT COUNT(*) FROM properties_final;")
total = cur.fetchone()[0]
print(f"Total rows in properties_final: {total}\n")

# ──────────────────────────────────────────────────────────────
# PRIMARY: areaname — the dedicated location/neighbourhood field
# ──────────────────────────────────────────────────────────────
print("="*70)
print("UNIQUE LOCATIONS — 'areaname' column (PRIMARY)")
print("="*70)
cur.execute("""
    SELECT areaname, COUNT(*) AS num_properties
    FROM properties_final
    WHERE areaname IS NOT NULL AND TRIM(areaname) != ''
    GROUP BY areaname
    ORDER BY num_properties DESC, areaname ASC;
""")
rows = cur.fetchall()
print(f"Total unique locations (areaname): {len(rows)}\n")
print(f"  {'Location':<50} | Properties")
print(f"  {'-'*50}-+-----------")
for i, (val, cnt) in enumerate(rows, 1):
    print(f"  {i:>3}. {str(val):<46} | {cnt}")

# ──────────────────────────────────────────────────────────────
# By city breakdown
# ──────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("CITY BREAKDOWN")
print("="*70)
cur.execute("""
    SELECT city, COUNT(DISTINCT areaname) AS unique_areas, COUNT(*) AS total_properties
    FROM properties_final
    WHERE city IS NOT NULL AND TRIM(city) != ''
    GROUP BY city
    ORDER BY total_properties DESC;
""")
city_rows = cur.fetchall()
for city, areas, props in city_rows:
    print(f"  {city:<20} — {areas} unique areas, {props} total properties")

# ──────────────────────────────────────────────────────────────
# Hyderabad-only unique areas
# ──────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("UNIQUE LOCATIONS — Hyderabad only")
print("="*70)
cur.execute("""
    SELECT areaname, COUNT(*) AS num_properties
    FROM properties_final
    WHERE city ILIKE '%Hyderabad%'
      AND areaname IS NOT NULL AND TRIM(areaname) != ''
    GROUP BY areaname
    ORDER BY num_properties DESC, areaname ASC;
""")
hyd_rows = cur.fetchall()
print(f"Total unique Hyderabad locations: {len(hyd_rows)}\n")
for i, (val, cnt) in enumerate(hyd_rows, 1):
    print(f"  {i:>3}. {str(val):<46} | {cnt}")

cur.close()
conn.close()
