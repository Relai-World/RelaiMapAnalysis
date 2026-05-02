"""
Find and fetch Google Place data for properties missing google_place_id
Uses property name, builder, and area to search
"""
from dotenv import load_dotenv
import os
from supabase import create_client
import requests
import time

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

def search_place(query, location=None):
    """Search for a place using Text Search API"""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': GOOGLE_API_KEY
    }
    if location:
        params['location'] = location
        params['radius'] = 5000  # 5km radius
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            result = data['results'][0]  # Get first result
            return {
                'place_id': result.get('place_id'),
                'name': result.get('name'),
                'rating': result.get('rating'),
                'user_ratings_total': result.get('user_ratings_total'),
                'address': result.get('formatted_address')
            }
        return None
    except Exception as e:
        print(f"  ❌ Error searching: {e}")
        return None

def update_property_place_data(property_id, place_data):
    """Update property with Google Place data"""
    try:
        supabase.table('unified_data_DataType_Raghu').update({
            'google_place_id': place_data['place_id'],
            'google_place_name': place_data['name'],
            'google_place_rating': str(place_data['rating']) if place_data.get('rating') else None,
            'google_place_user_ratings_total': str(place_data['user_ratings_total']) if place_data.get('user_ratings_total') else None,
            'google_place_address': place_data.get('address')
        }).eq('id', property_id).execute()
        return True
    except Exception as e:
        print(f"  ❌ Error updating: {e}")
        return False

# Check specific properties
properties_to_check = [
    {'id': 5128, 'name': 'IRIS', 'builder': 'Raghava Projects', 'area': 'Gachibowli'},
    {'id': 5120, 'name': 'IRIS', 'builder': 'Raghava Projects', 'area': 'Gachibowli'},
]

print("🔍 Searching for Google Places data...\n")

for prop in properties_to_check:
    print(f"📍 {prop['name']} by {prop['builder']} (ID: {prop['id']})")
    
    # Try different search queries
    queries = [
        f"{prop['name']} {prop['builder']} {prop['area']}",
        f"{prop['name']} {prop['area']} Hyderabad",
        f"{prop['builder']} {prop['name']}"
    ]
    
    place_data = None
    for query in queries:
        print(f"   Trying: {query}")
        place_data = search_place(query)
        if place_data:
            break
        time.sleep(0.2)
    
    if place_data:
        print(f"   ✅ Found: {place_data['name']}")
        if place_data.get('rating'):
            print(f"   ⭐ Rating: {place_data['rating']} ({place_data['user_ratings_total']} reviews)")
        else:
            print(f"   ⚠️ No rating available")
        
        # Update database
        if update_property_place_data(prop['id'], place_data):
            print(f"   ✅ Updated in database")
    else:
        print(f"   ❌ Not found")
    
    print()
    time.sleep(0.5)

print("Done!")
