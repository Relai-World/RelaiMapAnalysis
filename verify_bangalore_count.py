#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
}

# Get count
url = f"{supabase_url}/rest/v1/locations"
params = {'select': 'id,name', 'city': 'eq.Bangalore', 'order': 'id.asc'}
response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    locations = response.json()
    print(f"✅ Bangalore locations count: {len(locations)}")
    print(f"\nFirst 10:")
    for loc in locations[:10]:
        print(f"   ID {loc['id']}: {loc['name']}")
    print(f"\nLast 10:")
    for loc in locations[-10:]:
        print(f"   ID {loc['id']}: {loc['name']}")
else:
    print(f"❌ Error: {response.status_code}")
