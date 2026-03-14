import requests
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Get all locations using Supabase REST API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# First, let's check what tables exist
print("Checking available tables...")
print(f"URL: {SUPABASE_URL}/rest/v1/")

# Try different possible table names
table_names = ["locations", "location", "map_locations", "news_balanced_corpus"]

for table_name in table_names:
    print(f"\nTrying table: {table_name}")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit=5",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} records")
        if data:
            print(f"Columns: {list(data[0].keys())}")
    else:
        print(f"Error: {response.text[:200]}")

# Now get all locations
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/locations?select=id,name&order=id.asc",
    headers=headers
)

if response.status_code == 200:
    locations = response.json()
    
    print(f"Total locations found: {len(locations)}\n")
    print("="*70)
    
    # Format for Python list
    print("\nPython list format:")
    print("HYDERABAD_LOCATIONS = [")
    for i, loc in enumerate(locations):
        loc_id = loc['id']
        name = loc['name']
        if i < len(locations) - 1:
            print(f'    ({loc_id}, "{name}"),')
        else:
            print(f'    ({loc_id}, "{name}")')
    print("]")
    
    print("\n" + "="*70)
    print(f"\nTotal: {len(locations)} locations")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
