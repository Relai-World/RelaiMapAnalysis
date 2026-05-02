"""
Fetch Google Place ratings for properties that have google_place_id but missing ratings
"""
from dotenv import load_dotenv
import os
from supabase import create_client
import requests
import time

load_dotenv()

# Initialize Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

if not GOOGLE_API_KEY:
    print("❌ GOOGLE_PLACES_API_KEY not found in .env")
    exit(1)

def fetch_place_details(place_id):
    """Fetch place details from Google Places API"""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'fields': 'rating,user_ratings_total,name',
        'key': GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'OK':
            result = data.get('result', {})
            return {
                'rating': result.get('rating'),
                'user_ratings_total': result.get('user_ratings_total'),
                'name': result.get('name')
            }
        else:
            print(f"  ⚠️ API returned status: {data.get('status')}")
            return None
    except Exception as e:
        print(f"  ❌ Error fetching place details: {e}")
        return None

def update_property_rating(property_id, rating_data):
    """Update property with rating data"""
    try:
        supabase.table('unified_data_DataType_Raghu').update({
            'google_place_rating': str(rating_data['rating']) if rating_data['rating'] else None,
            'google_place_user_ratings_total': str(rating_data['user_ratings_total']) if rating_data['user_ratings_total'] else None
        }).eq('id', property_id).execute()
        return True
    except Exception as e:
        print(f"  ❌ Error updating database: {e}")
        return False

def main():
    print("🔍 Fetching properties with google_place_id but missing ratings...\n")
    
    # Get properties with place_id but no rating
    result = supabase.table('unified_data_DataType_Raghu').select(
        'id, projectname, buildername, google_place_id, google_place_name, google_place_rating'
    ).not_.is_('google_place_id', 'null').is_('google_place_rating', 'null').limit(50).execute()
    
    properties = result.data
    print(f"Found {len(properties)} properties to update\n")
    
    updated_count = 0
    failed_count = 0
    
    for prop in properties:
        print(f"📍 {prop['projectname']} (ID: {prop['id']})")
        print(f"   Place ID: {prop['google_place_id']}")
        
        # Fetch rating from Google
        rating_data = fetch_place_details(prop['google_place_id'])
        
        if rating_data and rating_data['rating']:
            print(f"   ⭐ Rating: {rating_data['rating']} ({rating_data['user_ratings_total']} reviews)")
            
            # Update database
            if update_property_rating(prop['id'], rating_data):
                print(f"   ✅ Updated in database")
                updated_count += 1
            else:
                failed_count += 1
        else:
            print(f"   ⚠️ No rating available")
            failed_count += 1
        
        print()
        
        # Rate limiting - Google allows 10 requests per second
        time.sleep(0.15)
    
    print(f"\n{'='*50}")
    print(f"✅ Successfully updated: {updated_count}")
    print(f"❌ Failed or no rating: {failed_count}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
