"""
Debug BHK values in the database
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

print("Debugging BHK values in Hitec City...")

# Check BHK values and their types
cur.execute("""
    SELECT bhk, COUNT(*), pg_typeof(bhk)
    FROM properties_final 
    WHERE LOWER(areaname) LIKE '%hitec%'
    GROUP BY bhk, pg_typeof(bhk)
    ORDER BY COUNT(*) DESC
""")

results = cur.fetchall()
print("\nBHK values, counts, and data types:")
for bhk, count, data_type in results:
    print(f"  BHK: '{bhk}' (type: {data_type}) - Count: {count}")

# Check specific BHK filtering
print("\n" + "="*50)
print("Testing BHK filtering queries:")

# Test exact match with string
cur.execute("""
    SELECT COUNT(*) 
    FROM properties_final 
    WHERE LOWER(areaname) LIKE '%hitec%' 
    AND CAST(bhk AS TEXT) = '2'
""")
count_2bhk_str = cur.fetchone()[0]
print(f"BHK = '2' (string): {count_2bhk_str} properties")

# Test exact match with number
cur.execute("""
    SELECT COUNT(*) 
    FROM properties_final 
    WHERE LOWER(areaname) LIKE '%hitec%' 
    AND bhk = '2.0'
""")
count_2bhk_num = cur.fetchone()[0]
print(f"BHK = '2.0': {count_2bhk_num} properties")

# Test with CAST to numeric
cur.execute("""
    SELECT COUNT(*) 
    FROM properties_final 
    WHERE LOWER(areaname) LIKE '%hitec%' 
    AND CAST(bhk AS NUMERIC) = 2
""")
count_2bhk_numeric = cur.fetchone()[0]
print(f"CAST(bhk AS NUMERIC) = 2: {count_2bhk_numeric} properties")

cur.close()
conn.close()