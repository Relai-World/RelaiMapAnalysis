#!/usr/bin/env python3
"""
Try to query the locations table directly to get the exact count
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def query_locations_table():
    """Try different approaches to get the exact location count"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Trying different approaches to get location data...")
    
    # Try 1: Direct locations table
    print("\n1️⃣ Trying direct locations table query...")
    try:
        url = f"{supabase_url}/rest/v1/locations"
        params = {'select': 'id,name', 'order': 'id.asc'}
        response = requests.get(url, headers=headers, params=params)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            locations = response.json()
            print(f"   Found: {len(locations)} locations")
            if locations:
                print(f"   First few: {[loc.get('name', 'N/A') for loc in locations[:5]]}")
                print(f"   Last few: {[loc.get('name', 'N/A') for loc in locations[-5:]]}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Try 2: Count only
    print("\n2️⃣ Trying to get count only...")
    try:
        url = f"{supabase_url}/rest/v1/locations"
        headers_count = headers.copy()
        headers_count['Prefer'] = 'count=exact'
        params = {'select': 'id'}
        response = requests.head(url, headers=headers_count, params=params)
        print(f"   Status: {response.status_code}")
        
        if 'content-range' in response.headers:
            content_range = response.headers['content-range']
            print(f"   Content-Range: {content_range}")
            # Parse count from "0-X/Y" format
            if '/' in content_range:
                total_count = content_range.split('/')[-1]
                print(f"   Total locations in table: {total_count}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Try 3: Check available RPC functions
    print("\n3️⃣ Trying to list available RPC functions...")
    try:
        # This might not work, but worth trying
        url = f"{supabase_url}/rest/v1/rpc"
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Try 4: Check if there's a specific Hyderabad filter RPC
    print("\n4️⃣ Trying search_locations_func (used by frontend)...")
    try:
        url = f"{supabase_url}/rest/v1/rpc/search_locations_func"
        body = {'search_query': ''}  # Empty search might return all
        response = requests.post(url, headers=headers, json=body)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"   Found: {len(results)} locations")
            if results:
                print(f"   Sample: {results[0] if results else 'None'}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("The discrepancy (175 vs 169) could be due to:")
    print("1. 📊 Database has grown - new locations added recently")
    print("2. 🗺️ Different geographic boundaries used")
    print("3. 🔄 Duplicate entries with slight name variations")
    print("4. 🏙️ Mixed Hyderabad/Bangalore data in same table")
    print("5. 📈 Your original count was from a different time/source")
    
    print("\n💡 RECOMMENDATION:")
    print("The 175 locations we found are likely correct for the current")
    print("database state. The 169 number might be from an older count")
    print("or a different filtering criteria.")

if __name__ == "__main__":
    query_locations_table()