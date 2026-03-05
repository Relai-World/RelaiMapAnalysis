import psycopg2, os, sys
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

PROJECT_IDS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

# First find ALL tables that reference locations
cur.execute("""
    SELECT tc.table_name, kcu.column_name 
    FROM information_schema.table_constraints tc 
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name 
    JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name 
    WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'locations'
""")
fk_tables = cur.fetchall()
print("Tables referencing locations:")
for t, c in fk_tables:
    print(f"  {t}.{c}")

# Delete from each referencing table first, then from locations
for loc_id in PROJECT_IDS:
    cur.execute("SELECT name FROM locations WHERE id = %s", (loc_id,))
    row = cur.fetchone()
    if not row:
        continue
    name = row[0]
    
    for table, col in fk_tables:
        cur.execute(f"DELETE FROM {table} WHERE {col} = %s", (loc_id,))
    
    cur.execute("DELETE FROM locations WHERE id = %s", (loc_id,))
    print(f"  REMOVED: ID:{loc_id} {name}")

conn.commit()

cur.execute("SELECT COUNT(*) FROM locations")
total = cur.fetchone()[0]
print(f"\nLocations remaining: {total}")

cur.close()
conn.close()
