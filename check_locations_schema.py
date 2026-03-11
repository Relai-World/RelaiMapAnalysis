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
    sslmode='require' if os.getenv('DB_HOST') != 'localhost' else 'prefer'
)

cur = conn.cursor()

# Check locations table schema
print('=== LOCATIONS TABLE COLUMNS ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'locations'
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

print('\n=== SAMPLE LOCATIONS ===')
cur.execute('SELECT * FROM locations LIMIT 5')
cols = [desc[0] for desc in cur.description]
print(f'Columns: {cols}')
for row in cur.fetchall():
    print(f'  {row}')

print('\n=== PRICE TRENDS SAMPLE ===')
cur.execute('SELECT * FROM price_trends LIMIT 3')
cols = [desc[0] for desc in cur.description]
print(f'Columns: {cols}')
for row in cur.fetchall():
    print(f'  {row}')

cur.close()
conn.close()
