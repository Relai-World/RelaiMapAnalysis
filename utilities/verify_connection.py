import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Show connection details (without password)
print("=" * 80)
print("DATABASE CONNECTION CHECK")
print("=" * 80)
print()

host = os.getenv('DB_HOST', 'localhost')
user = os.getenv('DB_USER', 'postgres')
dbname = os.getenv('DB_NAME', 'real_estate_intelligence')
port = os.getenv('DB_PORT', '5432')

print(f"Host: {host}")
print(f"User: {user}")
print(f"Database: {dbname}")
print(f"Port: {port}")
print()

try:
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=os.getenv('DB_PASSWORD', 'post@123'),
        dbname=dbname,
        port=port,
        sslmode='require' if host != 'localhost' else 'prefer'
    )
    
    cur = conn.cursor()
    
    # Get current database name
    cur.execute("SELECT current_database();")
    current_db = cur.fetchone()[0]
    print(f"✅ Connected to database: {current_db}")
    print()
    
    # List all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    print(f"Tables found ({len(tables)}):")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table[0]};")
        count = cur.fetchone()[0]
        print(f"  - {table[0]:30s} ({count:,} rows)")
    
    print()
    
    # Check if csv_properties exists
    if any(t[0] == 'csv_properties' for t in tables):
        print("✅ csv_properties table EXISTS")
    else:
        print("❌ csv_properties table DOES NOT EXIST")
        print()
        print("Let me create it now...")
        
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")

print("=" * 80)
