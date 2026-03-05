from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   
import psycopg2
import requests
import time

import os
import random
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Real Estate Intelligence API")

# Health Check Endpoint
@app.get("/")
def health_check():
    return {"status": "ok", "message": "West Hyderabad Intelligence API is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# DB CONNECTION
# ===============================
def get_db():
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "post@123")
    dbname = os.getenv("DB_NAME", "real_estate_intelligence")
    port = os.getenv("DB_PORT", "5432")

    return psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=dbname,
        port=port,
        sslmode='require' if host != 'localhost' else 'prefer'
    )

# Helper: Fetch Dynamic Facts (Original Marketing Style)
def fetch_dynamic_facts(cur, loc_id, s_score, g_score, i_score, default_s, default_g, default_i):
    # 1. Sentiment: "The Vibe"
    try:
        if s_score >= 0.4:
            s_fact = "🔥 <b>Investor Favorite:</b> High buzz driven by rapid commercial development."
        elif s_score >= 0.1:
            s_fact = "✅ <b>Positive Outlook:</b> Steady infrastructure upgrades boosting confidence."
        elif s_score >= -0.1:
            s_fact = "⚖️ <b>Balanced Market:</b> Stable demand with consistent long-term value."
        else:
            s_fact = "👀 <b>Value Pick:</b> Market consolidation offers unique entry points."
    except Exception:
        s_fact = default_s

    # 2. Growth: "The Driver"
    try:
        cur.execute("SELECT hospitals, schools, metro, airports FROM location_infrastructure WHERE location_id = %s", (loc_id,))
        row = cur.fetchone()
        if row:
            h, s, m, a = row
            if m > 0:
                g_fact = "🚇 <b>Super Connected:</b> Direct Metro access ensures unbeatable commute."
            elif a > 0:
                g_fact = "✈️ <b>Global Gateway:</b> Strategic proximity to International Airport."
            elif s > 5:
                g_fact = f"🏫 <b>Family Prime:</b> Surrounded by {s}+ top-tier international schools."
            elif h > 3:
                g_fact = "🏥 <b>Medical Hub:</b> World-class healthcare access within minutes."
            else:
                g_fact = "🏗️ <b>Developing Fast:</b> New roads and civic infra coming up."
        else:
            g_fact = default_g
    except Exception:
        g_fact = default_g

    # 3. Investment: "The Returns"
    try:
        cur.execute("SELECT year, avg_price_sqft FROM price_trends WHERE location_id = %s ORDER BY year ASC", (loc_id,))
        p_rows = cur.fetchall()
        if len(p_rows) >= 2:
            start = p_rows[0]
            end = p_rows[-1]
            years = max(1, end[0] - start[0])
            cagr = (pow(end[1] / start[1], 1/years) - 1) * 100
            
            if cagr > 12:
                i_fact = "🚀 <b>Skyrocketing:</b> Explosive annual growth track record."
            elif cagr > 8:
                i_fact = "💎 <b>Wealth Builder:</b> Strong consistent annual returns."
            else:
                i_fact = "🛡️ <b>Safe Bet:</b> Steady appreciation beating inflation."
        else:
            i_fact = default_i
    except Exception:
        i_fact = default_i

    return s_fact, g_fact, i_fact

# ===============================
# CORE INSIGHTS
# ===============================
@app.get("/api/v1/insights")
def insights():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                l.id,
                l.name,
                ST_X(l.geom) AS longitude,
                ST_Y(l.geom) AS latitude,
                li.avg_sentiment_score,
                li.growth_score,
                li.investment_score,
                (SELECT COUNT(*) FROM news_balanced_corpus WHERE location_id = l.id) as article_count
            FROM locations l
            JOIN location_insights li
              ON li.location_id = l.id
            ORDER BY l.name;
        """)
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            # Generate dynamic facts (Punchy Marketing Copy)
            # r[4] = sentiment, r[5] = growth, r[6] = investment
            s_fact, g_fact, i_fact = fetch_dynamic_facts(
                cur, 
                r[0], # id
                r[4], # s_score
                r[5], # g_score
                r[6], # i_score
                "Sentiment is stable across major news outlets.",
                "Infrastructure is developing steadily.",
                "Prices show consistent long-term appreciation."
            )

            results.append({
                "location_id": r[0],
                "location": r[1],
                "longitude": float(r[2]),
                "latitude": float(r[3]),
                "avg_sentiment": float(r[4]),
                "growth_score": float(r[5]),
                "investment_score": float(r[6]),
                "article_count": int(r[7]),
                "sentiment_summary": s_fact,
                "growth_summary": g_fact,
                "invest_summary": i_fact
            })

        cur.close()
        conn.close()

        return results
    except Exception as e:
        print(f"🔥 DATABASE ERROR: {e}")
        return {"error": str(e), "message": "Failed to connect to database or fetch insights"}

# ===============================
# SAFE OVERPASS COUNT
# ===============================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def safe_count(query: str) -> int:
    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "WestHyderabadIntel/1.0",
            "Referer": "http://localhost"
        }
        r = requests.post(OVERPASS_URL, data=query, timeout=25, headers=headers)
        if r.status_code != 200:
            return 0
        data = r.json()
        total = 0
        for el in data.get("elements", []):
            if "tags" in el and "total" in el["tags"]:
                total += int(el["tags"]["total"])
            elif "count" in el:
                total += int(el["count"]["total"])
        if total == 0 and len(data.get("elements", [])) > 5:
            return len(data["elements"])
        return total
    except Exception as e:
        print(f"🔥 Overpass Exception: {e}")
        return 0

# ===============================
# LOCATION INFRA COUNTS
# ===============================
@app.get("/api/v1/location/{location_id}/infra")
def location_infra(location_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT ST_Y(geom), ST_X(geom) FROM locations WHERE id = %s",
        (location_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"hospitals": 0, "schools": 0, "metro": 0, "airports": 0, "malls": 0}

    lat, lng = row
    base = "[out:json][timeout:25];(node(around:5000,{0},{1})[{{2}}];way(around:5000,{0},{1})[{{2}}];relation(around:5000,{0},{1})[{{2}}];);out count;"
    
    time.sleep(0.5) 
    return {
        "hospitals": safe_count(base.format(lat, lng, "amenity=hospital")),
        "schools": safe_count(base.format(lat, lng, "amenity=school")),
        "metro": safe_count(base.format(lat, lng, "railway=station")),
        "airports": safe_count(base.format(lat, lng, "aeroway=aerodrome")),
        "malls": safe_count(base.format(lat, lng, "shop=mall"))
    }

# ===============================
# PRICE TRENDS
# ===============================
@app.get("/api/v1/location/{location_id}/trends")
def get_location_trends(location_id: int):
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Fetch location name
        cur.execute("SELECT name FROM locations WHERE id = %s", (location_id,))
        name_row = cur.fetchone()
        location_name = name_row[0] if name_row else f"Location {location_id}"
        
        # Fetch richer dataset: quarter (e.g. '2024Q1'), price, min/max
        cur.execute("""
            SELECT quarter, average_price, min_price, max_price 
            FROM price_trends 
            WHERE location_id = %s 
            ORDER BY quarter ASC;
        """, (location_id,))
        
        rows = cur.fetchall()
        
        # Calculate growth metrics if enough data
        growth_yoy = 0.0
        cagr = 0.0
        
        if len(rows) >= 4:
            current_price = float(rows[-1][1])
            prev_year_price = float(rows[-5][1]) if len(rows) >= 5 else float(rows[0][1])
            
            if prev_year_price > 0:
                growth_yoy = round(((current_price - prev_year_price) / prev_year_price) * 100, 1)
            
            # Simple CAGR approximation over available years
            start_price = float(rows[0][1])
            years = len(rows) / 4
            if start_price > 0 and years > 0:
                cagr = round((pow(current_price / start_price, 1/years) - 1) * 100, 1)

        cur.close()
        conn.close()
        
        return {
            "location_id": location_id,
            "location": location_name,
            "growth_yoy": growth_yoy,
            "cagr": cagr,
            "trends": [
                {
                    "period": r[0], 
                    "price": float(r[1]),
                    "min": float(r[2]) if r[2] else 0,
                    "max": float(r[3]) if r[3] else 0
                } for r in rows
            ]
        }
    except Exception as e:
        print(f"🔥 TRENDS ERROR: {e}")
        return {"trends": [], "error": str(e)}

@app.get("/api/v1/market-trends")
def get_market_trends():
    """Get the average price trend across ALL locations (Hyderabad Baseline)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Aggregate across all locations per quarter
        cur.execute("""
            SELECT quarter, AVG(average_price) as avg_price
            FROM price_trends 
            GROUP BY quarter 
            ORDER BY quarter ASC;
        """)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{"period": r[0], "price": round(float(r[1]), 2)} for r in rows]
    except Exception as e:
        print(f"🔥 MARKET TRENDS ERROR: {e}")
        return []

# ===============================
# LOCATION COSTS
# ===============================
@app.get("/api/v1/location-costs")
def get_all_location_costs():
    """Get property cost statistics for all locations"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                location_name,
                property_count,
                avg_base_price,
                avg_price_sqft,
                min_base_price,
                max_base_price,
                min_price_sqft,
                max_price_sqft
            FROM location_costs
            ORDER BY location_name;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "location": r[0],
            "count": r[1],
            "avgBase": round(float(r[2]) / 10000000, 2),  # Convert to Crores
            "avgSqft": round(float(r[3]), 0),
            "minBase": round(float(r[4]) / 10000000, 2),  # Convert to Crores
            "maxBase": round(float(r[5]) / 10000000, 2),  # Convert to Crores
            "minSqft": round(float(r[6]), 0),
            "maxSqft": round(float(r[7]), 0)
        } for r in rows]
    except Exception as e:
        print(f"🔥 LOCATION COSTS ERROR: {e}")
        return {"error": str(e)}

@app.get("/api/v1/location-costs/{location_name}")
def get_location_cost(location_name: str):
    """Get property cost statistics for a specific location"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                location_name,
                property_count,
                avg_base_price,
                avg_price_sqft,
                min_base_price,
                max_base_price,
                min_price_sqft,
                max_price_sqft
            FROM location_costs
            WHERE location_name ILIKE %s;
        """, (location_name,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return {
                "location": row[0],
                "count": row[1],
                "avgBase": round(float(row[2]) / 10000000, 2),  # Convert to Crores
                "avgSqft": round(float(row[3]), 0),
                "minBase": round(float(row[4]) / 10000000, 2),  # Convert to Crores
                "maxBase": round(float(row[5]) / 10000000, 2),  # Convert to Crores
                "minSqft": round(float(row[6]), 0),
                "maxSqft": round(float(row[7]), 0)
            }
        else:
            return {"error": "Location not found"}
    except Exception as e:
        print(f"🔥 LOCATION COST ERROR: {e}")
        return {"error": str(e)}

# ===============================
# AMENITY LOCATIONS (WITH COORDINATES)
# ===============================
@app.get("/api/v1/location/{location_id}/amenities/{amenity_type}")
def get_amenity_locations(location_id: int, amenity_type: str):
    """
    Get detailed amenity locations with coordinates for mapping
    amenity_type: 'hospitals', 'schools', 'malls', 'restaurants', 'banks', 'atms', 'parks', 'gyms'
    Returns amenities within 4km with distance-based color coding
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT ST_Y(geom), ST_X(geom), name FROM locations WHERE id = %s",
        (location_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"error": "Location not found", "amenities": []}

    lat, lng, location_name = row

    # Map amenity types to Google Places types
    google_type_mapping = {
        'hospitals': 'hospital',
        'schools': 'school',
        'malls': 'shopping_mall',
        'restaurants': 'restaurant',
        'banks': 'bank',
        'atms': 'atm',
        'parks': 'park',
        'gyms': 'gym',
        'cafes': 'cafe',
        'metro': 'subway_station',
        'metro_stations': 'subway_station',
        'pharmacies': 'pharmacy',
        'supermarkets': 'supermarket'
    }

    if amenity_type not in google_type_mapping:
        return {"error": "Invalid amenity type", "amenities": []}

    g_type = google_type_mapping[amenity_type]
    api_key = "AIzaSyBi0vpchEjZNY3WL8fja0488QlXzhD6s-0"
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type={g_type}&key={api_key}"

    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return {"error": "Google API error", "amenities": []}

        data = r.json()
        amenities = []

        # Limit the number of results processed to save bandwidth and UI clutter
        for element in data.get("results", [])[:15]:
            geometry = element.get("geometry", {}).get("location", {})
            amenity_lat = geometry.get("lat")
            amenity_lng = geometry.get("lng")
            
            if not amenity_lat or not amenity_lng:
                continue

            name = element.get("name", f"Unnamed {amenity_type[:-1]}")

            # Calculate distance (simple Euclidean for small distances)
            import math
            distance_km = math.sqrt(
                ((amenity_lat - lat) * 111) ** 2 + 
                ((amenity_lng - lng) * 111 * math.cos(math.radians(lat))) ** 2
            )

            # Color coding based on distance (5km total)
            if distance_km <= 2.0:
                color = "green"  # Close (0-2 km)
            elif distance_km <= 3.5:
                color = "orange"  # Medium (2-3.5 km)
            else:
                color = "red"  # Far (3.5-5 km)

            amenities.append({
                "name": name,
                "latitude": amenity_lat,
                "longitude": amenity_lng,
                "distance_km": round(distance_km, 2),
                "color": color,
                "osm_id": element.get("place_id")
            })

        # Sort by distance
        amenities.sort(key=lambda x: x["distance_km"])

        return {
            "location": location_name,
            "location_lat": lat,
            "location_lng": lng,
            "amenity_type": amenity_type,
            "total_count": len(amenities),
            "amenities": amenities,
            "color_legend": {
                "green": "0-2 km (Close)",
                "orange": "2-3.5 km (Medium)",
                "red": "3.5-5 km (Far)"
            }
        }

    except Exception as e:
        print(f"🔥 Amenity Fetch Error: {e}")
        return {"error": str(e), "amenities": []}

# ===============================
# TELANGANA PROPERTY DATA APIs
# ===============================

@app.get("/api/v1/telangana/districts")
def get_telangana_districts():
    """Get all 33 Telangana districts with stats"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.name, d.code, d.region,
                   (SELECT COUNT(*) FROM telangana_mandals WHERE district_code = d.code) as mandals,
                   (SELECT COUNT(*) FROM telangana_villages WHERE district_code = d.code) as villages,
                   (SELECT COUNT(*) FROM telangana_market_values WHERE district_code = d.code) as price_records
            FROM telangana_districts d
            ORDER BY d.name;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "name": r[0], "code": r[1], "region": r[2],
            "mandals": r[3], "villages": r[4], "price_records": r[5]
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/districts/{district_code}/mandals")
def get_district_mandals(district_code: str):
    """Get all mandals for a district"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT m.name, m.code, m.district_name,
                   (SELECT COUNT(*) FROM telangana_villages WHERE mandal_code = m.code AND district_code = m.district_code) as villages
            FROM telangana_mandals m
            WHERE m.district_code = %s
            ORDER BY m.name;
        """, (district_code,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{"name": r[0], "code": r[1], "district": r[2], "villages": r[3]} for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/mandals/{district_code}/{mandal_code}/villages")
def get_mandal_villages(district_code: str, mandal_code: str):
    """Get all villages for a mandal"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT v.name, v.code, v.mandal_name, v.district_name
            FROM telangana_villages v
            WHERE v.district_code = %s AND v.mandal_code = %s
            ORDER BY v.name;
        """, (district_code, mandal_code))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{"name": r[0], "code": r[1], "mandal": r[2], "district": r[3]} for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/market-values")
def get_telangana_market_values(district: str = None, mandal: str = None, min_price: float = None, max_price: float = None, limit: int = 100):
    """Get market values with optional filters"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        query = "SELECT district, mandal, village, classification, price_per_sqyd, rate_type FROM telangana_market_values WHERE 1=1"
        params = []
        
        if district:
            query += " AND district ILIKE %s"
            params.append(f"%{district}%")
        if mandal:
            query += " AND mandal ILIKE %s"
            params.append(f"%{mandal}%")
        if min_price:
            query += " AND price_per_sqyd >= %s"
            params.append(min_price)
        if max_price:
            query += " AND price_per_sqyd <= %s"
            params.append(max_price)
        
        query += " ORDER BY price_per_sqyd DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "district": r[0], "mandal": r[1], "village": r[2],
            "classification": r[3], "price_per_sqyd": float(r[4]), "rate_type": r[5]
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/top-locations")
def get_telangana_top_locations(limit: int = 20):
    """Get top priced locations in Telangana"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT village, mandal, district, 
                   MAX(price_per_sqyd) as max_price,
                   MIN(price_per_sqyd) as min_price,
                   AVG(price_per_sqyd) as avg_price,
                   COUNT(*) as records
            FROM telangana_market_values
            WHERE price_per_sqyd > 0
            GROUP BY village, mandal, district
            ORDER BY max_price DESC
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "village": r[0], "mandal": r[1], "district": r[2],
            "max_price": float(r[3]), "min_price": float(r[4]),
            "avg_price": round(float(r[5]), 2), "records": r[6]
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/price-stats")
def get_telangana_price_stats():
    """Get price statistics by district"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT district,
                   COUNT(*) as records,
                   MIN(price_per_sqyd) as min_price,
                   MAX(price_per_sqyd) as max_price,
                   AVG(price_per_sqyd) as avg_price,
                   COUNT(DISTINCT mandal) as mandals,
                   COUNT(DISTINCT village) as villages
            FROM telangana_market_values
            WHERE price_per_sqyd > 0
            GROUP BY district
            ORDER BY max_price DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "district": r[0], "records": r[1],
            "min_price": float(r[2]), "max_price": float(r[3]),
            "avg_price": round(float(r[4]), 2),
            "mandals": r[5], "villages": r[6]
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/search")
def search_telangana_locations(q: str, limit: int = 50):
    """Search villages by name"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT v.name, v.mandal_name, v.district_name,
                   (SELECT MAX(price_per_sqyd) FROM telangana_market_values 
                    WHERE village = v.name AND mandal = v.mandal_name) as max_price
            FROM telangana_villages v
            WHERE v.name ILIKE %s
            ORDER BY v.name
            LIMIT %s;
        """, (f"%{q}%", limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{
            "village": r[0], "mandal": r[1], "district": r[2],
            "max_price": float(r[3]) if r[3] else None
        } for r in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/stats")
def get_telangana_overall_stats():
    """Get overall Telangana property data statistics"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        stats = {}
        
        cur.execute("SELECT COUNT(*) FROM telangana_districts")
        stats["districts"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM telangana_mandals")
        stats["mandals"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM telangana_villages")
        stats["villages"] = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM telangana_market_values")
        stats["market_values"] = cur.fetchone()[0]
        
        cur.execute("""
            SELECT MIN(price_per_sqyd), MAX(price_per_sqyd), AVG(price_per_sqyd)
            FROM telangana_market_values WHERE price_per_sqyd > 0
        """)
        price_row = cur.fetchone()
        if price_row and price_row[0]:
            stats["price_range"] = {
                "min": float(price_row[0]),
                "max": float(price_row[1]),
                "avg": round(float(price_row[2]), 2)
            }
        
        cur.close()
        conn.close()
        
        return stats
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/telangana/village/{village_id}/boundary")
def get_telangana_village_boundary(village_id: int):
    """Get boundary for a specific village"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, mandal_name, district_name,
                   ST_AsGeoJSON(COALESCE(boundary, ST_Buffer(centroid::geography, 1000)::geometry)) as geom,
                   ST_Y(centroid) as lat, ST_X(centroid) as lng
            FROM telangana_villages
            WHERE id = %s
        """, (village_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return {"error": "Village not found"}
        
        result = {
            "village": row[0],
            "mandal": row[1],
            "district": row[2],
            "latitude": row[4],
            "longitude": row[5]
        }
        
        if row[3]:
            import json
            result["boundary"] = json.loads(row[3])
        
        return result
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/locations/{location_id}/boundary")
def get_location_boundary(location_id: int):
    """Get boundary for a specific location (accurate polygons)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, ST_AsGeoJSON(boundary) as boundary_geojson FROM locations WHERE id = %s AND boundary IS NOT NULL",
            (location_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return {"error": "Location not found or no boundary available"}
        
        import json
        return {
            "id": row[0],
            "name": row[1],
            "boundary": json.loads(row[2])
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/locations/boundaries")
def get_all_boundaries():
    """Get all location boundaries as GeoJSON FeatureCollection"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, ST_AsGeoJSON(boundary) as boundary_geojson FROM locations WHERE boundary IS NOT NULL ORDER BY name"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        features = []
        import json
        for row in rows:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": row[0],
                    "name": row[1]
                },
                "geometry": json.loads(row[2])
            })
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "count": len(features)
        }
    except Exception as e:
        return {"error": str(e)}


    """Get all village boundaries as GeoJSON FeatureCollection"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        query = """
            SELECT id, name, mandal_name, district_name,
                   ST_AsGeoJSON(COALESCE(boundary, ST_Buffer(centroid::geography, 500)::geometry)) as geom
            FROM telangana_villages
            WHERE centroid IS NOT NULL
        """
        params = []
        
        if district:
            query += " AND district_name ILIKE %s"
            params.append(f"%{district}%")
        
        query += " LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        features = []
        for row in rows:
            if row[4]:
                import json
                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": row[0],
                        "village": row[1],
                        "mandal": row[2],
                        "district": row[3]
                    },
                    "geometry": json.loads(row[4])
                })
        
        return {
            "type": "FeatureCollection",
            "features": features,
            "count": len(features)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
