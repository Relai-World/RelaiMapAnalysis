import psycopg2, os, sys
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

fk = [('raw_scraped_data','location_id'),('location_insights','location_id'),('price_trends','location_id'),('location_infrastructure','location_id'),('location_costs','location_id')]

# Remove "Electronics City Phase 1" (dup of Electronic City Phase 1)
# Remove "Phase 8th JP Nagar" (dup of JP Nagar Phase 7)
remove = [312, 376]
for lid in remove:
    cur.execute("SELECT name FROM locations WHERE id = %s", (lid,))
    row = cur.fetchone()
    if row:
        for t, c in fk:
            cur.execute(f"DELETE FROM {t} WHERE {c} = %s", (lid,))
        cur.execute("DELETE FROM locations WHERE id = %s", (lid,))
        print(f"Removed: ID:{lid} {row[0]}")

# Fix trailing comma in "Electronic City Phase 2,"
cur.execute("UPDATE locations SET name = 'Electronic City Phase 2' WHERE id = 311")
print("Fixed: 'Electronic City Phase 2,' -> 'Electronic City Phase 2'")

conn.commit()
cur.execute("SELECT COUNT(*) FROM locations")
print(f"Locations remaining: {cur.fetchone()[0]}")
cur.close()
conn.close()
