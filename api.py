from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
import time
import psycopg2

import os
import random
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase REST client (no DB password needed)
_supabase: Client = None
def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key and key != "your_service_role_key_here":
            _supabase = create_client(url, key)
    return _supabase

# PostgreSQL direct connection for properties
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 6543),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

app = FastAPI(title="Real Estate Intelligence API")

# Health Check Endpoint
@app.get("/")
def health_check():
    return {"status": "ok", "message": "West Hyderabad Intelligence API is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_methods=["*"],
    allow_headers=["*"],
)

# FUTURE DEVELOPMENT ENDPOINT - Fixed encoding issue
@app.get("/api/v1/future-development/{location_id}")
def get_future_development(location_id: int):
    """Get future development data for a location"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            print("❌ Supabase client not initialized - check SUPABASE_URL and SUPABASE_KEY")
            return {
                'success': False,
                'error': 'Supabase configuration missing',
                'developments': [],
                'total_count': 0
            }
        
        # Fetch future development data for the location
        response = supabase.table('future_development_scrap').select(
            'id, location_name, source, content, published_at, year_mentioned, scraped_at'
        ).eq('location_id', location_id).order('published_at', desc=True).limit(10).execute()
        
        developments = response.data
        
        # Process and format the data
        formatted_developments = []
        for dev in developments:
            formatted_developments.append({
                'id': dev['id'],
                'source': dev['source'],
                'content': dev['content'][:200] + '...' if len(dev['content']) > 200 else dev['content'],
                'full_content': dev['content'],
                'published_at': dev['published_at'],
                'year_mentioned': dev['year_mentioned'],
                'scraped_at': dev['scraped_at']
            })
        
        return {
            'success': True,
            'location_id': location_id,
            'developments': formatted_developments,
            'total_count': len(formatted_developments)
        }
        
    except Exception as e:
        print(f"❌ Error fetching future development: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'developments': [],
            'total_count': 0
        }

# ===============================
# AMENITY LOCATIONS - GOOGLE PLACES API ONLY
# ===============================
@app.get("/api/v1/amenities/{amenity_type}")
def get_amenities(amenity_type: str, lat: float, lng: float, limit: int = 10):
    """
    Get amenities from Google Places API (Legacy)
    Query params: lat, lng, limit (default: 10)
    amenity_type: 'hospitals', 'schools', 'malls', 'restaurants', 'banks', 'parks', 'metro'
    """
    print(f"🔍 Amenities Request: type={amenity_type}, lat={lat}, lng={lng}, limit={limit}")
    
    # Debug: Confirm limit parameter
    print(f"🎯 LIMIT PARAMETER RECEIVED: {limit}")
    print(f"🎯 LIMIT TYPE: {type(limit)}")
    
    # Map amenity types to Google Places API types
    google_type_mapping = {
        'hospitals': 'hospital',
        'schools': 'school', 
        'malls': 'shopping_mall',
        'restaurants': 'restaurant',
        'banks': 'bank',
        'parks': 'park',
        'metro': 'subway_station'
    }

    if amenity_type not in google_type_mapping:
        print(f"❌ Invalid amenity type: {amenity_type}")
        return {"error": "Invalid amenity type", "amenities": []}

    g_type = google_type_mapping[amenity_type]
    
    # Force reload .env file to get the correct API key
    from dotenv import load_dotenv
    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        print("❌ Google Places API key not found in environment")
        return {"error": "Google Places API key not configured", "amenities": []}
    
    print(f"✅ API Key loaded: {api_key[:10]}...")
    
    # Use Legacy Places API only
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    params = {
        'location': f'{lat},{lng}',
        'radius': 5000,
        'type': g_type,
        'key': api_key
    }
    
    print(f"🌐 Legacy Places API URL: {url}")
    print(f"📋 Request params: {params}")

    try:
        print("📡 Making request to Legacy Places API...")
        r = requests.get(url, params=params, timeout=30)
        print(f"📊 Response Status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code} - {r.text}")
            return {"error": f"Google API HTTP {r.status_code}", "amenities": []}

        data = r.json()
        print(f"📋 API Response status: {data.get('status')}")
        
        if data.get('status') != 'OK':
            error_msg = data.get('error_message', f"Status: {data.get('status')}")
            print(f"❌ API Error: {error_msg}")
            return {"error": f"Google Places API: {error_msg}", "amenities": []}
        
        results = data.get("results", [])
        print(f"📍 Found {len(results)} raw results from Google")
        
        amenities = []

        # Process results
        for i, result in enumerate(results):
            name = result.get("name", f"Unnamed {amenity_type[:-1]}")
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            
            place_lat = location.get("lat")
            place_lng = location.get("lng")
            
            if not place_lat or not place_lng:
                print(f"⚠️ Skipping result {i}: missing coordinates")
                continue

            # Calculate distance using Haversine formula
            import math
            R = 6371  # Earth's radius in km
            lat1, lng1 = math.radians(lat), math.radians(lng)
            lat2, lng2 = math.radians(place_lat), math.radians(place_lng)
            
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance_km = R * c

            # Color coding based on distance
            if distance_km <= 2.0:
                color = "green"
            elif distance_km <= 3.5:
                color = "orange"
            else:
                color = "red"

            amenities.append({
                "name": name,
                "latitude": place_lat,
                "longitude": place_lng,
                "distance_km": round(distance_km, 2),
                "color": color
            })

        # Sort by distance
        amenities.sort(key=lambda x: x["distance_km"])
        
        # Apply limit
        print(f"🎯 BEFORE LIMIT: {len(amenities)} amenities")
        amenities = amenities[:limit]
        print(f"🎯 AFTER LIMIT: {len(amenities)} amenities (limit was {limit})")
        
        print(f"✅ Processed {len(amenities)} amenities successfully (limited to {limit})")
        
        return {
            "amenity_type": amenity_type,
            "total_count": len(amenities),
            "amenities": amenities,
            "api_used": "Legacy Places API"
        }

    except requests.exceptions.Timeout:
        print("❌ Request timeout to Google Places API")
        return {"error": "Request timeout", "amenities": []}
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return {"error": f"Request error: {str(e)}", "amenities": []}
    except Exception as e:
        print(f"🔥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "amenities": []}





def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points using Haversine formula"""
    import math
    R = 6371  # Earth's radius in km
    lat1, lng1 = math.radians(lat1), math.radians(lng1)
    lat2, lng2 = math.radians(lat2), math.radians(lng2)
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def get_distance_color(distance_km):
    """Get color based on distance"""
    if distance_km <= 2.0:
        return "green"
    elif distance_km <= 3.5:
        return "orange"
    else:
        return "red"
    """
    Get amenities from Google Places API (New)
    Query params: lat, lng
    amenity_type: 'hospitals', 'schools', 'malls', 'restaurants', 'banks', 'parks', 'metro'
    """
    print(f"🔍 Amenities Request: type={amenity_type}, lat={lat}, lng={lng}")
    
    # Map amenity types to Google Places API (New) types
    google_type_mapping = {
        'hospitals': 'hospital',
        'schools': 'school', 
        'malls': 'shopping_mall',
        'restaurants': 'restaurant',
        'banks': 'bank',
        'parks': 'park',
        'metro': 'subway_station'
    }

    if amenity_type not in google_type_mapping:
        print(f"❌ Invalid amenity type: {amenity_type}")
        return {"error": "Invalid amenity type", "amenities": []}

    g_type = google_type_mapping[amenity_type]
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        print("❌ Google Places API key not found in environment")
        return {"error": "Google Places API key not configured", "amenities": []}
    
    print(f"✅ API Key loaded: {api_key[:10]}...")
    
    # New Places API endpoint and request format
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.displayName,places.location,places.types,places.primaryType'
    }
    
    # New API uses JSON POST request instead of GET
    request_body = {
        "includedTypes": [g_type],
        "maxResultCount": 15,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": 5000.0
            }
        }
    }
    
    print(f"🌐 New Places API URL: {url}")
    print(f"📋 Request body: {request_body}")

    try:
        print("📡 Making request to Google Places API (New)...")
        r = requests.post(url, json=request_body, headers=headers, timeout=30)
        print(f"📊 Response Status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code} - {r.text}")
            return {"error": f"Google API HTTP {r.status_code}", "amenities": []}

        data = r.json()
        print(f"📋 API Response: {data}")
        
        # Check for error in response
        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            print(f"❌ API Error: {error_msg}")
            return {"error": f"Google Places API: {error_msg}", "amenities": []}
        
        places = data.get("places", [])
        print(f"📍 Found {len(places)} raw results from Google")
        
        amenities = []

        # Process results
        for i, place in enumerate(places):
            display_name = place.get("displayName", {})
            location = place.get("location", {})
            
            name = display_name.get("text", f"Unnamed {amenity_type[:-1]}")
            place_lat = location.get("latitude")
            place_lng = location.get("longitude")
            
            if not place_lat or not place_lng:
                print(f"⚠️ Skipping result {i}: missing coordinates")
                continue

            # Calculate distance using Haversine formula
            import math
            R = 6371  # Earth's radius in km
            lat1, lng1 = math.radians(lat), math.radians(lng)
            lat2, lng2 = math.radians(place_lat), math.radians(place_lng)
            
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance_km = R * c

            # Color coding based on distance
            if distance_km <= 2.0:
                color = "green"
            elif distance_km <= 3.5:
                color = "orange"
            else:
                color = "red"

            amenities.append({
                "name": name,
                "latitude": place_lat,
                "longitude": place_lng,
                "distance_km": round(distance_km, 2),
                "color": color
            })

        # Sort by distance
        amenities.sort(key=lambda x: x["distance_km"])
        
        print(f"✅ Processed {len(amenities)} amenities successfully")
        
        return {
            "amenity_type": amenity_type,
            "total_count": len(amenities),
            "amenities": amenities
        }

    except requests.exceptions.Timeout:
        print("❌ Request timeout to Google Places API")
        return {"error": "Request timeout", "amenities": []}
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return {"error": f"Request error: {str(e)}", "amenities": []}
    except Exception as e:
        print(f"🔥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "amenities": []}

# ===============================
# TELANGANA ENDPOINTS REMOVED
# All Telangana registration data endpoints have been removed as they are not used by the frontend.
# ===============================


# ===============================
# UNUSED ENDPOINTS REMOVED
# Properties endpoints removed - frontend uses Supabase RPC directly
# ===============================


# Removed unused properties endpoint - frontend uses Supabase RPC directly

def get_property_detail(property_id: int):
    """Get full detail for a single property from unified_data_DataType_Raghu table."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id, projectname, buildername, project_type, communitytype,
                status, project_status, isavailable, configsoldoutstatus,
                city, state,
                areaname, projectlocation, google_place_name,
                google_place_address, google_place_location,
                google_maps_location, mobile_google_map_url,
                baseprojectprice, price_per_sft, total_buildup_area,
                floor_rise_charges, floor_rise_amount_per_floor,
                floor_rise_applicable_above_floor_no, facing_charges,
                preferential_location_charges,
                preferential_location_charges_conditions,
                amount_for_extra_car_parking, price_per_sft_update_date,
                project_launch_date, possession_date, construction_status,
                construction_material, total_land_area, number_of_towers,
                number_of_floors, number_of_flats_per_floor,
                total_number_of_units, open_space, carpet_area_percentage,
                floor_to_ceiling_height,
                bhk, sqfeet, sqyard, facing, no_of_car_parkings,
                external_amenities, specification, powerbackup,
                no_of_passenger_lift, no_of_service_lift,
                visitor_parking, ground_vehicle_movement,
                main_door_height, available_banks_for_loan, home_loan,
                builder_age, builder_completed_properties,
                builder_ongoing_projects, builder_operating_locations,
                builder_origin_city, builder_total_properties,
                builder_upcoming_properties,
                poc_name, poc_contact, poc_role,
                alternative_contact, useremail,
                images, google_place_rating, google_place_user_ratings_total,
                rera_number, projectbrochure
            FROM unified_data_DataType_Raghu
            WHERE id = %s;
        """, (property_id,))
        r = cur.fetchone()
        cur.close()
        conn.close()

        if not r:
            return {"error": "Property not found"}

        cols = [
            "id","projectname","buildername","project_type","communitytype",
            "status","project_status","isavailable","configsoldoutstatus",
            "city","state",
            "areaname","projectlocation","google_place_name",
            "google_place_address","google_place_location",
            "google_maps_location","mobile_google_map_url",
            "baseprojectprice","price_per_sft","total_buildup_area",
            "floor_rise_charges","floor_rise_amount_per_floor",
            "floor_rise_applicable_above_floor_no","facing_charges",
            "preferential_location_charges",
            "preferential_location_charges_conditions",
            "amount_for_extra_car_parking","price_per_sft_update_date",
            "project_launch_date","possession_date","construction_status",
            "construction_material","total_land_area","number_of_towers",
            "number_of_floors","number_of_flats_per_floor",
            "total_number_of_units","open_space","carpet_area_percentage",
            "floor_to_ceiling_height",
            "bhk","sqfeet","sqyard","facing","no_of_car_parkings",
            "external_amenities","specification","powerbackup",
            "no_of_passenger_lift","no_of_service_lift",
            "visitor_parking","ground_vehicle_movement",
            "main_door_height","available_banks_for_loan","home_loan",
            "builder_age","builder_completed_properties",
            "builder_ongoing_projects","builder_operating_locations",
            "builder_origin_city","builder_total_properties",
            "builder_upcoming_properties",
            "poc_name","poc_contact","poc_role",
            "alternative_contact","useremail",
            "images","google_place_rating","google_place_user_ratings_total",
            "rera_number","projectbrochure"
        ]

        result = {}
        for i, col in enumerate(cols):
            val = r[i]
            # Handle numeric conversions safely for unified_data_DataType_Raghu data
            if val and col in ["baseprojectprice", "price_per_sft", "google_place_rating"] and isinstance(val, str):
                try:
                    val = float(val) if val != 'None' and val != '' and val is not None else None
                except (ValueError, TypeError):
                    val = None
            elif hasattr(val, '__float__') and not isinstance(val, (int, float)):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = None
            result[col] = val
        
        # Return in the same format as the list endpoint
        property_card = {
            'id': result.get('id'),
            'projectname': result.get('projectname'),
            'buildername': result.get('buildername'),
            'project_type': result.get('project_type'),
            'bhk': result.get('bhk'),
            'sqfeet': result.get('sqfeet'),
            'price_per_sft': result.get('price_per_sft'),
            'construction_status': result.get('construction_status'),
            'areaname': result.get('areaname'),
            'images': result.get('images'),
            'full_details': result
        }
        
        return property_card
    except Exception as e:
        print(f"🔥 PROPERTY DETAIL ERROR: {e}")
        return {"error": str(e)}

# Mount static files to serve the frontend (must be last)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)