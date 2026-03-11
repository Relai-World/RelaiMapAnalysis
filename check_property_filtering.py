"""
Check property data and BHK filtering issues
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
print("CHECKING PROPERTY TABLES FOR BHK DATA")
print("="*80)

# Check properties_final table
print("\n1. PROPERTIES_FINAL TABLE")
print("-" * 40)

try:
    # Get column info
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'properties_final'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print(f"Columns ({len(columns)}):")
    for col, dtype in columns:
        print(f"  - {col} ({dtype})")
    
    # Check total records
    cur.execute("SELECT COUNT(*) FROM properties_final")
    total = cur.fetchone()[0]
    print(f"\nTotal records: {total}")
    
    # Check BHK-related columns
    bhk_columns = [col for col, _ in columns if 'bhk' in col.lower() or 'bedroom' in col.lower() or 'room' in col.lower()]
    print(f"\nBHK-related columns: {bhk_columns}")
    
    if bhk_columns:
        for col in bhk_columns:
            cur.execute(f"SELECT {col}, COUNT(*) FROM properties_final WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY COUNT(*) DESC LIMIT 10")
            values = cur.fetchall()
            print(f"\n{col} distribution:")
            for val, count in values:
                print(f"  {val}: {count} records")
    
    # Check for any column that might contain BHK info
    print("\nChecking for BHK patterns in text columns...")
    text_columns = [col for col, dtype in columns if 'text' in dtype or 'varchar' in dtype or 'character' in dtype]
    
    for col in text_columns[:5]:  # Check first 5 text columns
        try:
            cur.execute(f"""
                SELECT {col}, COUNT(*) 
                FROM properties_final 
                WHERE {col} ILIKE '%bhk%' OR {col} ILIKE '%bedroom%'
                GROUP BY {col} 
                ORDER BY COUNT(*) DESC 
                LIMIT 5
            """)
            results = cur.fetchall()
            if results:
                print(f"\n{col} with BHK patterns:")
                for val, count in results:
                    print(f"  {val}: {count}")
        except:
            continue

except Exception as e:
    print(f"Error with properties_final: {e}")

# Check real_estate_projects table
print("\n\n2. REAL_ESTATE_PROJECTS TABLE")
print("-" * 40)

try:
    # Get column info
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'real_estate_projects'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print(f"Columns ({len(columns)}):")
    for col, dtype in columns:
        print(f"  - {col} ({dtype})")
    
    # Check total records
    cur.execute("SELECT COUNT(*) FROM real_estate_projects")
    total = cur.fetchone()[0]
    print(f"\nTotal records: {total}")
    
    # Check BHK-related columns
    bhk_columns = [col for col, _ in columns if 'bhk' in col.lower() or 'bedroom' in col.lower() or 'room' in col.lower()]
    print(f"\nBHK-related columns: {bhk_columns}")
    
    if bhk_columns:
        for col in bhk_columns:
            cur.execute(f"SELECT {col}, COUNT(*) FROM real_estate_projects WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY COUNT(*) DESC LIMIT 10")
            values = cur.fetchall()
            print(f"\n{col} distribution:")
            for val, count in values:
                print(f"  {val}: {count} records")

except Exception as e:
    print(f"Error with real_estate_projects: {e}")

# Check csv_properties table
print("\n\n3. CSV_PROPERTIES TABLE")
print("-" * 40)

try:
    # Get column info
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'csv_properties'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print(f"Columns ({len(columns)}):")
    for col, dtype in columns:
        print(f"  - {col} ({dtype})")
    
    # Check total records
    cur.execute("SELECT COUNT(*) FROM csv_properties")
    total = cur.fetchone()[0]
    print(f"\nTotal records: {total}")
    
    # Check BHK-related columns
    bhk_columns = [col for col, _ in columns if 'bhk' in col.lower() or 'bedroom' in col.lower() or 'room' in col.lower()]
    print(f"\nBHK-related columns: {bhk_columns}")
    
    if bhk_columns:
        for col in bhk_columns:
            cur.execute(f"SELECT {col}, COUNT(*) FROM csv_properties WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY COUNT(*) DESC LIMIT 10")
            values = cur.fetchall()
            print(f"\n{col} distribution:")
            for val, count in values:
                print(f"  {val}: {count} records")

except Exception as e:
    print(f"Error with csv_properties: {e}")

cur.close()
conn.close()