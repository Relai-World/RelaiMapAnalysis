import psycopg2
import os
from dotenv import load_dotenv

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

print("=" * 80)
print("TABLES IN YOUR DATABASE")
print("=" * 80)
print()

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
    ORDER BY table_name;
""")

tables = cur.fetchall()

if tables:
    for table in tables:
        table_name = table[0]
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        
        print(f"📋 {table_name}")
        print(f"   Rows: {count:,}")
        print()
else:
    print("No tables found!")

print("=" * 80)

# Check if csv_properties exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'csv_properties'
    );
""")

exists = cur.fetchone()[0]

if exists:
    print("✅ csv_properties table EXISTS")
    cur.execute("SELECT COUNT(*) FROM csv_properties;")
    count = cur.fetchone()[0]
    print(f"   Total records: {count:,}")
else:
    print("❌ csv_properties table NOT FOUND")
    print()
    print("The table was not created. This could be because:")
    print("  1. The script didn't run successfully")
    print("  2. Database connection issue")
    print("  3. Permission issue")

print("=" * 80)

cur.close()
conn.close()
