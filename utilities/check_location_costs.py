import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432"),
    sslmode='require' if os.getenv("DB_HOST", "localhost") != 'localhost' else 'prefer'
)

cur = conn.cursor()

# Check if table exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'location_costs'
    );
""")

exists = cur.fetchone()[0]

if exists:
    print("✅ location_costs table EXISTS")
    cur.execute("SELECT * FROM location_costs ORDER BY location_name;")
    rows = cur.fetchall()
    print(f"\nFound {len(rows)} locations:\n")
    for row in rows:
        print(f"  - {row[1]}: {row[2]} properties, Avg ₹{row[3]/10000000:.2f} Cr")
else:
    print("❌ location_costs table DOES NOT EXIST")
    print("\nRun: python load_location_costs.py")

cur.close()
conn.close()
