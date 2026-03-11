import requests
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# First check what location names we have
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'post@123'),
    dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
    port=os.getenv('DB_PORT', '5432'),
    sslmode='require' if os.getenv('DB_HOST') != 'localhost' else 'prefer'
)

cur = conn.cursor()

print('=== Testing Location Name Match ===')
# Get a sample location
cur.execute("SELECT id, name FROM locations WHERE id = 202")
loc = cur.fetchone()
print(f'Location ID: {loc[0]}, Name: {loc[1]}')

# Check if this name exists in price_trends
cur.execute("SELECT location FROM price_trends WHERE LOWER(location) = LOWER(%s)", (loc[1],))
trend = cur.fetchone()
if trend:
    print(f'Found in price_trends: {trend[0]}')
else:
    print('NOT FOUND in price_trends')
    # Check what similar names exist
    cur.execute("SELECT location FROM price_trends WHERE location ILIKE %s", (f'%{loc[1][:5]}%',))
    similar = cur.fetchall()
    print(f'Similar names in price_trends: {[s[0] for s in similar]}')

cur.close()
conn.close()

# Test the API endpoint
print('\n=== Testing API Endpoint ===')
try:
    response = requests.get('http://127.0.0.1:8000/api/v1/location/202/trends')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'Error: {e}')
