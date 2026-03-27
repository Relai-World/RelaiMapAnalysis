from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# CORS must be added before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoint - for UptimeRobot monitoring
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "West Hyderabad Intelligence API is running"}

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

# ===============================
# TELANGANA ENDPOINTS REMOVED
# All Telangana registration data endpoints have been removed as they are not used by the frontend.
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

# Mount static files to serve the frontend (must be last)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)