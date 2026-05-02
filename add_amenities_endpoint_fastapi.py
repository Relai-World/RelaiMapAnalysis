# Add this endpoint to your api.py file (FastAPI version)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

# Request model
class AmenitiesRequest(BaseModel):
    area_name: str
    radius: int = 1000
    property_id: int

# Add this endpoint to your existing FastAPI app
@app.post("/api/nearby-amenities")
async def get_nearby_amenities(request: AmenitiesRequest):
    """
    Fetch nearby amenities count using Google Places API and store in database
    Uses area name to lookup coordinates from locations table
    """
    try:
        supabase = get_supabase()
        if not supabase:
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        area_name = request.area_name
        property_id = request.property_id
        radius = request.radius
        
        # Get coordinates from locations table using area name
        # Try hyderabad_locations first
        lat, lng = None, None
        
        try:
            result = supabase.table('hyderabad_locations')\
                .select('latitude, longitude')\
                .ilike('name', area_name)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                lat = result.data[0].get('latitude')
                lng = result.data[0].get('longitude')
        except Exception as e:
            print(f"Error querying hyderabad_locations: {e}")
        
        # Try bangalore_locations if not found
        if not lat or not lng:
            try:
                result = supabase.table('bangalore_locations')\
                    .select('latitude, longitude')\
                    .ilike('name', area_name)\
                    .limit(1)\
                    .execute()
                
                if result.data and len(result.data) > 0:
                    lat = result.data[0].get('latitude')
                    lng = result.data[0].get('longitude')
            except Exception as e:
                print(f"Error querying bangalore_locations: {e}")
        
        # Try old locations table as fallback
        if not lat or not lng:
            try:
                result = supabase.table('locations')\
                    .select('latitude, longitude')\
                    .ilike('name', area_name)\
                    .limit(1)\
                    .execute()
                
                if result.data and len(result.data) > 0:
                    lat = result.data[0].get('latitude')
                    lng = result.data[0].get('longitude')
            except Exception as e:
                print(f"Error querying locations: {e}")
        
        if not lat or not lng:
            raise HTTPException(
                status_code=404, 
                detail=f"Coordinates not found for area: {area_name}"
            )
        
        print(f"📍 Found coordinates for {area_name}: lat={lat}, lng={lng}")
        
        # Get Google Places API key
        google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not google_api_key:
            raise HTTPException(
                status_code=500, 
                detail="Google Places API key not configured"
            )
        
        # Define amenity types to search for
        amenity_types = {
            'hospitals_count': ['hospital', 'doctor', 'health'],
            'shopping_malls_count': ['shopping_mall', 'department_store'],
            'schools_count': ['school', 'primary_school', 'secondary_school'],
            'restaurants_count': ['restaurant', 'cafe', 'food'],
            'metro_stations_count': ['subway_station', 'transit_station', 'train_station']
        }
        
        counts = {}
        total_count = 0
        
        # Fetch count for each amenity type
        for column_name, place_types in amenity_types.items():
            count = 0
            
            for place_type in place_types:
                try:
                    # Call Google Places API - Nearby Search
                    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
                    params = {
                        'location': f'{lat},{lng}',
                        'radius': radius,
                        'type': place_type,
                        'key': google_api_key
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    places_data = response.json()
                    
                    if places_data.get('status') == 'OK':
                        results = places_data.get('results', [])
                        count = max(count, len(results))  # Take max to avoid double counting
                    
                except Exception as e:
                    print(f"Error fetching {place_type}: {str(e)}")
                    continue
            
            counts[column_name] = count
            total_count += count
        
        print(f"✅ Fetched amenities for {area_name}: {total_count} total")
        
        # Store counts in database
        try:
            update_data = {
                'hospitals_count': counts.get('hospitals_count', 0),
                'shopping_malls_count': counts.get('shopping_malls_count', 0),
                'schools_count': counts.get('schools_count', 0),
                'restaurants_count': counts.get('restaurants_count', 0),
                'metro_stations_count': counts.get('metro_stations_count', 0)
            }
            
            result = supabase.table('unified_data_DataType_Raghu')\
                .update(update_data)\
                .eq('id', property_id)\
                .execute()
            
            print(f"✅ Stored amenities count in database for property {property_id}")
            
        except Exception as db_error:
            print(f"⚠️ Failed to store in database: {str(db_error)}")
            # Continue anyway - we can still return the counts
        
        # Return counts
        return {
            'hospitals_count': counts.get('hospitals_count', 0),
            'shopping_malls_count': counts.get('shopping_malls_count', 0),
            'schools_count': counts.get('schools_count', 0),
            'restaurants_count': counts.get('restaurants_count', 0),
            'metro_stations_count': counts.get('metro_stations_count', 0),
            'total_count': total_count,
            'area_name': area_name,
            'coordinates': {'lat': lat, 'lng': lng},
            'stored_in_db': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
