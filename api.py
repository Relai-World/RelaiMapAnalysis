from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import time
# Removed psycopg2 - using Supabase REST API only

import os
import random
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(override=True)

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

# All database operations now use Supabase REST API only

app = FastAPI(title="Real Estate Intelligence API")

# CORS Configuration - Allow both GitHub Pages and custom domain
# Load allowed origins from environment variable
frontend_origin_env = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in frontend_origin_env.split(",")]

# Add common development ports for local testing
if os.getenv("ENVIRONMENT", "production") == "development":
    allowed_origins.extend([
        "http://localhost:8000", "http://127.0.0.1:8000",
        "http://localhost:5500", "http://127.0.0.1:5500",  # Live Server
        "http://localhost:3000", "http://127.0.0.1:3000"   # Common dev port
    ])

# Always allow both production domains (GitHub Pages and custom domain)
production_domains = [
    "https://analytics.relai.world",
    "https://relai-world.github.io"
]

for domain in production_domains:
    if domain not in allowed_origins:
        allowed_origins.append(domain)

print(f"🌐 CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health Check Endpoint - for UptimeRobot monitoring
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "West Hyderabad Intelligence API is running"}

# Supabase Config Endpoint - Serves credentials to frontend securely
@app.get("/api/config/supabase")
def get_supabase_config():
    """Serve Supabase credentials to frontend (anon key is safe to expose)"""
    return {
        "url": os.getenv("SUPABASE_URL"),
        "key": os.getenv("SUPABASE_KEY")
    }

# INTELLIGENCE SCORES WITH BENCHMARKING
@app.get("/api/v1/intelligence-scores/{location_id}")
def get_intelligence_scores(location_id: int):
    """Get intelligence scores with city-wide benchmarking for a location"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            return {
                'success': False,
                'error': 'Supabase configuration missing'
            }
        
        # Call the SQL function
        response = supabase.rpc('get_location_intelligence_scores', {'loc_id': location_id}).execute()
        
        if not response.data or len(response.data) == 0:
            return {
                'success': False,
                'error': 'Location not found'
            }
        
        data = response.data[0]
        
        return {
            'success': True,
            'location_id': data['location_id'],
            'location_name': data['location_name'],
            'scores': {
                'sentiment': {
                    'score': data['sentiment_score'],
                    'percentile': data['sentiment_percentile'],
                    'city_avg': data['city_avg_sentiment'],
                    'label': data['sentiment_label']
                },
                'growth': {
                    'score': data['growth_score'],
                    'percentile': data['growth_percentile'],
                    'city_avg': data['city_avg_growth'],
                    'label': data['growth_label']
                },
                'investment': {
                    'score': data['investment_score'],
                    'percentile': data['investment_percentile'],
                    'city_avg': data['city_avg_investment'],
                    'label': data['investment_label']
                }
            },
            'benchmark': {
                'total_locations': data['total_locations']
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching intelligence scores: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

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
    Get amenities from Google Places API
    Query params: lat, lng, limit (default: 10)
    amenity_type: 'hospitals', 'schools', 'malls', 'restaurants', 'banks', 'parks', 'metro'
    """
    print(f"🔍 Amenities Request: type={amenity_type}, lat={lat}, lng={lng}, limit={limit}")
    
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

            # Calculate distance using shared utility function
            distance_km = calculate_distance(lat, lng, place_lat, place_lng)
            color = get_distance_color(distance_km)

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

# ===============================
# TELANGANA ENDPOINTS REMOVED
# All Telangana registration data endpoints have been removed as they are not used by the frontend.
# ===============================





# ===============================
# UTILITY FUNCTIONS
# ===============================

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


# ===============================
# COMMUTE ANALYZER - GOOGLE MAPS API
# ===============================

@app.get("/api/search-place")
def search_place(query: str):
    """Search for places using Google Places Autocomplete API"""
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {"success": False, "error": "Google Maps API key not configured"}
        
        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            "input": query,
            "key": api_key,
            "components": "country:in",  # Restrict to India
            "types": "establishment"  # Focus on businesses/offices
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("status") == "OK":
            suggestions = []
            for prediction in data.get("predictions", []):
                suggestions.append({
                    "place_id": prediction["place_id"],
                    "description": prediction["description"],
                    "main_text": prediction["structured_formatting"]["main_text"],
                    "secondary_text": prediction["structured_formatting"].get("secondary_text", "")
                })
            return {"success": True, "suggestions": suggestions}
        else:
            return {"success": False, "error": data.get("status")}
            
    except Exception as e:
        print(f"❌ Error in search_place: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/nearby-places")
def nearby_places(lat: float, lng: float, keyword: str, radius: int = 50000, place_type: str = None):
    """Search for nearby places - with proper filtering for railway vs metro"""
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {"success": False, "error": "Google Maps API key not configured"}
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "rankby": "distance",
            "keyword": keyword,
            "key": api_key
        }
        
        if place_type:
            params["type"] = place_type
        
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"🔍 Searching for '{keyword}' near ({lat:.4f}, {lng:.4f})")
        print(f"   API Status: {data.get('status')}")
        
        if data.get("status") == "OK":
            from math import radians, sin, cos, sqrt, atan2
            
            def calculate_distance(lat1, lng1, lat2, lng2):
                R = 6371
                dlat = radians(lat2 - lat1)
                dlng = radians(lng2 - lng1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            
            places = []
            
            for place in data.get("results", []):
                place_types = place.get("types", [])
                place_name = place["name"].lower()
                
                # CRITICAL FILTERING: Distinguish railway from metro
                is_metro = any(t in place_types for t in ["subway_station", "light_rail_station"]) or "metro" in place_name
                is_railway = "train_station" in place_types and not is_metro
                
                # Skip based on what we're searching for
                if keyword and "railway" in keyword.lower():
                    # Looking for railway - skip metro stations
                    if is_metro:
                        print(f"   ❌ Skipping metro station: {place['name']}")
                        continue
                    if not is_railway:
                        print(f"   ❌ Skipping non-railway: {place['name']} (types: {place_types})")
                        continue
                
                elif keyword and "metro" in keyword.lower():
                    # Looking for metro - skip railway stations
                    if is_railway and not is_metro:
                        print(f"   ❌ Skipping railway station: {place['name']}")
                        continue
                
                place_lat = place["geometry"]["location"]["lat"]
                place_lng = place["geometry"]["location"]["lng"]
                distance = calculate_distance(lat, lng, place_lat, place_lng)
                
                places.append({
                    "place_id": place["place_id"],
                    "name": place["name"],
                    "lat": place_lat,
                    "lng": place_lng,
                    "vicinity": place.get("vicinity", ""),
                    "types": place_types,
                    "distance_km": round(distance, 2)
                })
            
            places.sort(key=lambda x: x["distance_km"])
            
            print(f"✅ Found {len(places)} valid places after filtering:")
            for i, p in enumerate(places[:5]):
                print(f"   {i+1}. {p['name']} - {p['distance_km']} km (types: {p['types'][:2]})")
            
            return {"success": True, "places": places}
        else:
            print(f"❌ API Error: {data.get('status')}")
            return {"success": False, "error": data.get("status"), "places": []}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "places": []}


@app.get("/api/directions")
def get_directions(origin_lat: float, origin_lng: float, dest_place_id: str):
    """Get directions from property to office using Google Directions API"""
    try:
        print(f"🔍 Getting directions from ({origin_lat}, {origin_lng}) to place_id: {dest_place_id}")
        
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("❌ Google Maps API key not configured")
            return {"success": False, "error": "Google Maps API key not configured"}
        
        origin = f"{origin_lat},{origin_lng}"
        destination = f"place_id:{dest_place_id}"
        
        routes = {}
        
        # 1. Driving route (with traffic)
        print("🚗 Fetching driving route...")
        driving_url = "https://maps.googleapis.com/maps/api/directions/json"
        driving_params = {
            "origin": origin,
            "destination": destination,
            "mode": "driving",
            "departure_time": "now",  # For traffic data
            "key": api_key
        }
        driving_response = requests.get(driving_url, params=driving_params)
        driving_data = driving_response.json()
        print(f"🚗 Driving API status: {driving_data.get('status')}")
        
        if driving_data.get("status") == "OK":
            route = driving_data["routes"][0]
            leg = route["legs"][0]
            
            # Extract step-by-step directions
            steps = []
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("html_instructions", ""),
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "maneuver": step.get("maneuver", "")
                })
            
            routes["driving"] = {
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "duration_in_traffic": leg.get("duration_in_traffic", {}).get("text", leg["duration"]["text"]),
                "summary": route["summary"],
                "polyline": route["overview_polyline"]["points"],
                "steps": steps,
                "start_address": leg.get("start_address", ""),
                "end_address": leg.get("end_address", "")
            }
        
        # 2. Transit route (Metro/Bus)
        transit_url = "https://maps.googleapis.com/maps/api/directions/json"
        transit_params = {
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "transit_mode": "rail|bus",  # Metro and bus
            "key": api_key
        }
        transit_response = requests.get(transit_url, params=transit_params)
        transit_data = transit_response.json()
        
        if transit_data.get("status") == "OK":
            route = transit_data["routes"][0]
            leg = route["legs"][0]
            
            # Determine if it's metro or bus based on transit details
            transit_modes = set()
            steps = []
            for step in leg.get("steps", []):
                step_info = {
                    "instruction": step.get("html_instructions", ""),
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "travel_mode": step.get("travel_mode", "")
                }
                
                if step.get("travel_mode") == "TRANSIT":
                    transit_detail = step.get("transit_details", {})
                    vehicle_type = transit_detail.get("line", {}).get("vehicle", {}).get("type", "")
                    transit_modes.add(vehicle_type)
                    
                    step_info["transit"] = {
                        "line": transit_detail.get("line", {}).get("name", ""),
                        "vehicle": vehicle_type,
                        "departure_stop": transit_detail.get("departure_stop", {}).get("name", ""),
                        "arrival_stop": transit_detail.get("arrival_stop", {}).get("name", ""),
                        "num_stops": transit_detail.get("num_stops", 0)
                    }
                
                steps.append(step_info)
            
            routes["transit"] = {
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "summary": route["summary"],
                "polyline": route["overview_polyline"]["points"],
                "transit_modes": list(transit_modes),
                "steps": steps,
                "start_address": leg.get("start_address", ""),
                "end_address": leg.get("end_address", "")
            }
        
        # 3. Bus-only route
        bus_url = "https://maps.googleapis.com/maps/api/directions/json"
        bus_params = {
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "transit_mode": "bus",
            "key": api_key
        }
        bus_response = requests.get(bus_url, params=bus_params)
        bus_data = bus_response.json()
        
        if bus_data.get("status") == "OK":
            route = bus_data["routes"][0]
            leg = route["legs"][0]
            
            # Extract steps for bus route
            steps = []
            for step in leg.get("steps", []):
                step_info = {
                    "instruction": step.get("html_instructions", ""),
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "travel_mode": step.get("travel_mode", "")
                }
                
                if step.get("travel_mode") == "TRANSIT":
                    transit_detail = step.get("transit_details", {})
                    step_info["transit"] = {
                        "line": transit_detail.get("line", {}).get("name", ""),
                        "departure_stop": transit_detail.get("departure_stop", {}).get("name", ""),
                        "arrival_stop": transit_detail.get("arrival_stop", {}).get("name", ""),
                        "num_stops": transit_detail.get("num_stops", 0)
                    }
                
                steps.append(step_info)
            
            routes["bus"] = {
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "summary": route["summary"],
                "polyline": route["overview_polyline"]["points"],
                "steps": steps,
                "start_address": leg.get("start_address", ""),
                "end_address": leg.get("end_address", "")
            }
        
        return {"success": True, "routes": routes}
        
    except Exception as e:
        print(f"❌ Error in get_directions: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# All endpoints now use Supabase REST API only - no direct database connections

# Custom handler for PMTiles files to support HTTP Range requests
from fastapi import Request, Response
from fastapi.responses import FileResponse
import os
from pathlib import Path

@app.get("/maptiles/{filename:path}")
async def serve_pmtiles(filename: str, request: Request):
    """Serve PMTiles files with Range request support"""
    file_path = Path("frontend/maptiles") / filename
    
    if not file_path.exists():
        return Response(status_code=404, content="File not found")
    
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range header (e.g., "bytes=0-1023")
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if len(range_match) > 1 and range_match[1] else file_size - 1
        
        # Read the requested byte range
        with open(file_path, "rb") as f:
            f.seek(start)
            data = f.read(end - start + 1)
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(data)),
            "Content-Type": "application/octet-stream",
        }
        return Response(content=data, status_code=206, headers=headers)
    else:
        # Serve full file
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            headers={"Accept-Ranges": "bytes"}
        )

# =====================================================
# AMENITIES API ENDPOINT
# =====================================================

class AmenitiesRequest(BaseModel):
    area_name: str
    radius: int = 1000
    property_id: int

@app.post("/api/nearby-amenities")
@app.options("/api/nearby-amenities")
async def get_nearby_amenities(request: AmenitiesRequest = None):
    """
    Fetch nearby amenities count using Google Places API and store in database
    Uses area name to lookup coordinates from locations table
    """
    # Handle OPTIONS request for CORS
    if request is None:
        return {"status": "ok"}
    
    try:
        supabase = get_supabase()
        if not supabase:
            return {"error": "Supabase not configured"}, 500
        
        area_name = request.area_name
        property_id = request.property_id
        radius = request.radius
        
        print(f"📍 Fetching amenities for {area_name} (property {property_id})")
        
        # Get coordinates from locations table using area name
        lat, lng = None, None
        
        # Query locations table
        try:
            result = supabase.table('locations')\
                .select('name, geom')\
                .ilike('name', f'%{area_name}%')\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                geom = result.data[0].get('geom')
                # Extract coordinates from POINT geometry string
                # Format: "POINT(78.3730556 17.4587912)"
                if geom and 'POINT' in geom:
                    coords = geom.replace('POINT(', '').replace(')', '').split()
                    if len(coords) == 2:
                        lng = float(coords[0])
                        lat = float(coords[1])
                        print(f"✅ Found {area_name} in locations: lat={lat}, lng={lng}")
        except Exception as e:
            print(f"⚠️ Error querying locations: {e}")
        
        if not lat or not lng:
            print(f"❌ No coordinates found for area: {area_name}")
            return {"error": f"Coordinates not found for area: {area_name}"}, 404
        
        # Get Google Places API key
        google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not google_api_key:
            return {"error": "Google Places API key not configured"}, 500
        
        # Define amenity types to search for
        amenity_types = {
            'hospitals_count': ['hospital', 'doctor'],
            'shopping_malls_count': ['shopping_mall'],
            'schools_count': ['school'],
            'restaurants_count': ['restaurant', 'cafe'],
            'metro_stations_count': ['subway_station', 'transit_station']
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
                    elif places_data.get('status') == 'ZERO_RESULTS':
                        pass  # No results, keep count as is
                    else:
                        print(f"⚠️ Google API status for {place_type}: {places_data.get('status')}")
                    
                except Exception as e:
                    print(f"❌ Error fetching {place_type}: {str(e)}")
                    continue
            
            counts[column_name] = count
            total_count += count
        
        print(f"✅ Fetched amenities for {area_name}: H:{counts.get('hospitals_count')} S:{counts.get('schools_count')} M:{counts.get('shopping_malls_count')} R:{counts.get('restaurants_count')} Metro:{counts.get('metro_stations_count')}")
        
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
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"error": str(e)}, 500

# Test GET endpoint to verify routing works
@app.get("/api/nearby-amenities-test")
def test_amenities():
    """Test endpoint to verify API routing works"""
    return {"message": "API routing works!", "status": "ok"}

# Mount static files to serve the frontend (must be last)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)