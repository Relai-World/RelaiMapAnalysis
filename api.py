from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import psycopg2
import requests
import time

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
    dbname = os.getenv("DB_NAME", "postgres")
    port = os.getenv("DB_PORT", "5432")

    return psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=dbname,
        port=port,
        sslmode='require' if host != 'localhost' else 'prefer',
        connect_timeout=10
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
    # Note: location_infrastructure table not available in new schema
    # Using default growth fact
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
            WITH property_stats AS (
                SELECT 
                    LOWER(areaname) as area_lower,
                    areaname as original_area,
                    COUNT(*) as property_count,
                    AVG(CAST(price_per_sft AS NUMERIC)) as avg_price_per_sft,
                    MIN(CAST(price_per_sft AS NUMERIC)) as min_price_per_sft,
                    MAX(CAST(price_per_sft AS NUMERIC)) as max_price_per_sft
                FROM unified_data_DataType_Raghu 
                WHERE price_per_sft IS NOT NULL 
                    AND price_per_sft != 'None' 
                    AND price_per_sft != ''
                    AND CAST(price_per_sft AS NUMERIC) > 0
                GROUP BY LOWER(areaname), areaname
            ),
            location_property_matches AS (
                SELECT 
                    l.id as location_id,
                    l.name as location_name,
                    SUM(ps.property_count) as total_property_count,
                    AVG(ps.avg_price_per_sft) as avg_price_per_sft,
                    MIN(ps.min_price_per_sft) as min_price_per_sft,
                    MAX(ps.max_price_per_sft) as max_price_per_sft
                FROM locations l
                LEFT JOIN property_stats ps ON (
                    LOWER(ps.original_area) = LOWER(l.name)
                    OR LOWER(REPLACE(ps.original_area, ' ', '')) = LOWER(REPLACE(l.name, ' ', ''))
                    OR ps.original_area ILIKE l.name
                    OR l.name ILIKE ps.original_area
                )
                GROUP BY l.id, l.name
            ),
            article_stats AS (
                SELECT 
                    location_id,
                    COUNT(*) as article_count
                FROM news_balanced_corpus_1 
                GROUP BY location_id
            )
            SELECT
                l.id,
                l.name,
                ST_X(l.geom) AS longitude,
                ST_Y(l.geom) AS latitude,
                COALESCE(li.avg_sentiment_score, 0) as avg_sentiment_score,
                COALESCE(li.growth_score, 0) as growth_score,
                COALESCE(li.investment_score, 0) as investment_score,
                COALESCE(a.article_count, 0) as article_count,
                COALESCE(lpm.avg_price_per_sft, 0) as avg_property_price,
                COALESCE(lpm.total_property_count, 0) as property_count,
                COALESCE(lpm.min_price_per_sft, 0) as min_property_price,
                COALESCE(lpm.max_price_per_sft, 0) as max_property_price
            FROM locations l
            LEFT JOIN location_insights li ON li.location_id = l.id
            LEFT JOIN location_property_matches lpm ON lpm.location_id = l.id
            LEFT JOIN article_stats a ON a.location_id = l.id
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

            # Generate property cost summary
            avg_price = float(r[8]) if r[8] else 0
            property_count = int(r[9]) if r[9] else 0
            min_price = float(r[10]) if r[10] else 0
            max_price = float(r[11]) if r[11] else 0
            
            if property_count > 0:
                if min_price == max_price:
                    price_summary = f"Properties priced at ₹{avg_price:,.0f}/sqft ({property_count} properties available)"
                else:
                    price_summary = f"Properties range from ₹{min_price:,.0f} to ₹{max_price:,.0f}/sqft (avg ₹{avg_price:,.0f}/sqft, {property_count} properties)"
            else:
                price_summary = "No property pricing data available"

            results.append({
                "location_id": r[0],
                "location": r[1],
                "longitude": float(r[2]),
                "latitude": float(r[3]),
                "avg_sentiment": float(r[4]),
                "growth_score": float(r[5]),
                "investment_score": float(r[6]),
                "article_count": int(r[7]),
                "avg_property_price": avg_price,
                "property_count": property_count,
                "min_property_price": min_price,
                "max_property_price": max_price,
                "price_summary": price_summary,
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
# LOCATION SEARCH (from news corpus)
# ===============================
@app.get("/api/v1/search")
def search_locations(q: str = ""):
    if not q or len(q.strip()) < 1:
        return []

    # Use psycopg2 to get distinct locations and avoid Supabase REST deduplication/RLS issues
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Use a subquery to get distinct locations matching the query
        # Using %q% to match substrings, not just prefixes
        search_term = f"%{q.strip()}%"
        
        cur.execute("""
            SELECT location_name, MIN(location_id) as location_id
            FROM news_balanced_corpus_1
            WHERE location_name ILIKE %s
            GROUP BY location_name
            ORDER BY location_name
            LIMIT 10
        """, (search_term,))
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return [{"location_name": r[0], "location_id": r[1]} for r in rows]
    except Exception as e:
        print(f"🔥 SEARCH FALLBACK ERROR: {e}")
        return []

@app.get("/api/v1/search/debug")
def search_debug():
    sb = get_supabase()
    if sb:
        try:
            # Check table counts across known tables
            tables = ["news_balanced_corpus_1", "news_balanced_corpus", "locations"]
            info = {}
            for t in tables:
                try:
                    res = sb.table(t).select("*", count="exact").limit(1).execute()
                    info[t] = res.count
                except Exception as te:
                    info[t] = f"error: {te}"
            return {"tables": info, "source": "supabase_rest"}
        except Exception as e:
            return {"error": str(e), "source": "supabase_rest"}
    return {"error": "Supabase client not configured — add SUPABASE_KEY to .env"}

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
        
        # Fetch location name from locations table (column is 'name', not 'location')
        cur.execute("SELECT name FROM locations WHERE id = %s", (location_id,))
        name_row = cur.fetchone()
        if not name_row:
            return {"error": "Location not found"}
        
        location_name = name_row[0]
        
        # Fetch price trends from new schema (location name + year columns)
        cur.execute("""
            SELECT location, year_2020, year_2021, year_2022, year_2023, year_2024, year_2025, year_2026
            FROM price_trends 
            WHERE LOWER(location) = LOWER(%s)
        """, (location_name,))
        
        row = cur.fetchone()
        
        if not row:
            cur.close()
            conn.close()
            return {"error": "No price trends data available for this location"}
        
        # Build trends array from year columns
        trends_data = []
        years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
        prices = [row[1], row[2], row[3], row[4], row[5], row[6], row[7]]
        
        for i, year in enumerate(years):
            if prices[i]:  # Only include if price exists
                trends_data.append({
                    "year": year,
                    "price": int(prices[i])
                })
        
        # Calculate growth metrics
        growth_yoy = 0.0
        cagr = 0.0
        
        if len(trends_data) >= 2:
            current_price = trends_data[-1]["price"]
            start_price = trends_data[0]["price"]
            years_span = trends_data[-1]["year"] - trends_data[0]["year"]
            
            # YoY growth (last year vs previous year)
            if len(trends_data) >= 2:
                prev_price = trends_data[-2]["price"]
                if prev_price > 0:
                    growth_yoy = round(((current_price - prev_price) / prev_price) * 100, 1)
            
            # CAGR calculation
            if start_price > 0 and years_span > 0:
                cagr = round((pow(current_price / start_price, 1/years_span) - 1) * 100, 1)

        cur.close()
        conn.close()
        
        return {
            "location_id": location_id,
            "location": location_name,
            "growth_yoy": growth_yoy,
            "cagr": cagr,
            "trends": trends_data
        }
        
    except Exception as e:
        print(f"Error fetching trends: {e}")
        return {"error": str(e)}

@app.get("/api/v1/market-trends")
def get_market_trends():
    """Get the average price trend across ALL locations (Hyderabad Baseline)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Calculate average across all locations for each year
        cur.execute("""
            SELECT 
                AVG(year_2020) as avg_2020,
                AVG(year_2021) as avg_2021,
                AVG(year_2022) as avg_2022,
                AVG(year_2023) as avg_2023,
                AVG(year_2024) as avg_2024,
                AVG(year_2025) as avg_2025,
                AVG(year_2026) as avg_2026
            FROM price_trends
        """)
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return []
        
        # Build response array
        years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
        result = []
        for i, year in enumerate(years):
            if row[i]:
                result.append({
                    "year": year,
                    "price": round(float(row[i]), 2)
                })
        
        return result
    except Exception as e:
        print(f"🔥 MARKET TRENDS ERROR: {e}")
        return []

# ===============================
# LOCATION COSTS
# ===============================
@app.get("/api/v1/location-costs")
def get_all_location_costs():
    """Get property cost statistics for all locations - USES unified_data_DataType_Raghu with optimized fuzzy matching"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Use the same optimized approach as insights endpoint
        cur.execute("""
            WITH property_stats AS (
                SELECT 
                    LOWER(areaname) as area_lower,
                    areaname as original_area,
                    COUNT(*) as property_count,
                    AVG(CAST(price_per_sft AS NUMERIC)) as avg_price_per_sft,
                    MIN(CAST(price_per_sft AS NUMERIC)) as min_price_per_sft,
                    MAX(CAST(price_per_sft AS NUMERIC)) as max_price_per_sft,
                    AVG(CAST(baseprojectprice AS NUMERIC)) as avg_base_price
                FROM unified_data_DataType_Raghu 
                WHERE price_per_sft IS NOT NULL 
                    AND price_per_sft != 'None' 
                    AND price_per_sft != ''
                    AND CAST(price_per_sft AS NUMERIC) > 0
                GROUP BY LOWER(areaname), areaname
            ),
            location_property_matches AS (
                SELECT 
                    l.name as location_name,
                    SUM(ps.property_count) as total_property_count,
                    AVG(ps.avg_price_per_sft) as avg_price_per_sft,
                    MIN(ps.min_price_per_sft) as min_price_per_sft,
                    MAX(ps.max_price_per_sft) as max_price_per_sft,
                    AVG(ps.avg_base_price) as avg_base_price
                FROM locations l
                LEFT JOIN property_stats ps ON (
                    LOWER(ps.original_area) = LOWER(l.name)
                    OR LOWER(REPLACE(ps.original_area, ' ', '')) = LOWER(REPLACE(l.name, ' ', ''))
                    OR ps.original_area ILIKE l.name
                    OR l.name ILIKE ps.original_area
                )
                WHERE ps.property_count IS NOT NULL
                GROUP BY l.name
                HAVING SUM(ps.property_count) > 0
            )
            SELECT 
                location_name,
                total_property_count,
                avg_price_per_sft,
                min_price_per_sft,
                max_price_per_sft,
                avg_base_price
            FROM location_property_matches
            ORDER BY avg_price_per_sft DESC;
        """)
        
        rows = cur.fetchall()
        results = []
        
        for row in rows:
            results.append({
                "location": row[0],
                "count": row[1],
                "avgBase": round(float(row[5]) / 10000000, 2) if row[5] else 0,  # Convert to Crores
                "avgSqft": round(float(row[2]), 0),
                "minBase": round(float(row[3]) / 10000000, 2) if row[3] else 0,  # Actual MIN base price
                "maxBase": round(float(row[4]) / 10000000, 2) if row[4] else 0,  # Actual MAX base price
                "minSqft": round(float(row[3]), 0),
                "maxSqft": round(float(row[4]), 0)
            })
        
        cur.close()
        conn.close()
        return results
        
    except Exception as e:
        print(f"🔥 LOCATION COSTS ERROR: {e}")
        return {"error": str(e)}

@app.get("/api/v1/location-costs/{location_name}")
def get_location_cost(location_name: str):
    """Get property cost statistics for a specific location - USES unified_data_DataType_Raghu data"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                %s as search_name,
                'Hyderabad' as city,
                COUNT(*) as property_count,
                AVG(CAST(price_per_sft AS NUMERIC)) as avg_price_per_sft,
                MIN(CAST(price_per_sft AS NUMERIC)) as min_price_per_sft,
                MAX(CAST(price_per_sft AS NUMERIC)) as max_price_per_sft,
                AVG(CAST(baseprojectprice AS NUMERIC)) as avg_base_price,
                MIN(CAST(baseprojectprice AS NUMERIC)) as min_base_price,
                MAX(CAST(baseprojectprice AS NUMERIC)) as max_base_price
            FROM unified_data_DataType_Raghu 
            WHERE (LOWER(areaname) = LOWER(%s)
                   OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(%s, ' ', ''))
                   OR areaname ILIKE %s || ', %%'
                   OR %s ILIKE areaname)
                AND price_per_sft IS NOT NULL 
                AND price_per_sft != 'None' 
                AND price_per_sft != ''
                AND CAST(price_per_sft AS NUMERIC) > 0
        """, (location_name, location_name, location_name, location_name, location_name))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row and row[2] > 0:  # Check if property_count > 0
            return {
                "location": row[0],
                "count": row[2],
                "avgBase": round(float(row[6]) / 10000000, 2) if row[6] else 0,  # avg in Crores
                "avgSqft": round(float(row[3]), 0),
                "minBase": round(float(row[7]) / 10000000, 2) if row[7] else 0,  # actual min
                "maxBase": round(float(row[8]) / 10000000, 2) if row[8] else 0,  # actual max
                "minSqft": round(float(row[4]), 0),
                "maxSqft": round(float(row[5]), 0)
            }
        else:
            return {"error": "Location not found"}
    except Exception as e:
        print(f"🔥 LOCATION COST ERROR: {e}")
        return {"error": str(e)}

# ===============================
# PROPERTY COSTS FROM unified_data_DataType_Raghu
# ===============================
@app.get("/api/v1/property-costs")
def get_all_property_costs():
    """Get property cost statistics from unified_data_DataType_Raghu table for all locations with optimized fuzzy matching"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Use the same optimized approach as insights endpoint
        cur.execute("""
            WITH property_stats AS (
                SELECT 
                    LOWER(areaname) as area_lower,
                    areaname as original_area,
                    COUNT(*) as property_count,
                    AVG(CAST(price_per_sft AS NUMERIC)) as avg_price_per_sft,
                    MIN(CAST(price_per_sft AS NUMERIC)) as min_price_per_sft,
                    MAX(CAST(price_per_sft AS NUMERIC)) as max_price_per_sft,
                    AVG(CAST(baseprojectprice AS NUMERIC)) as avg_base_price,
                    COUNT(DISTINCT buildername) as builder_count
                FROM unified_data_DataType_Raghu 
                WHERE price_per_sft IS NOT NULL 
                    AND price_per_sft != 'None' 
                    AND price_per_sft != ''
                    AND CAST(price_per_sft AS NUMERIC) > 0
                GROUP BY LOWER(areaname), areaname
            ),
            location_property_matches AS (
                SELECT 
                    l.name as location_name,
                    SUM(ps.property_count) as total_property_count,
                    AVG(ps.avg_price_per_sft) as avg_price_per_sft,
                    MIN(ps.min_price_per_sft) as min_price_per_sft,
                    MAX(ps.max_price_per_sft) as max_price_per_sft,
                    AVG(ps.avg_base_price) as avg_base_price,
                    SUM(ps.builder_count) as builder_count
                FROM locations l
                LEFT JOIN property_stats ps ON (
                    LOWER(ps.original_area) = LOWER(l.name)
                    OR LOWER(REPLACE(ps.original_area, ' ', '')) = LOWER(REPLACE(l.name, ' ', ''))
                    OR ps.original_area ILIKE l.name
                    OR l.name ILIKE ps.original_area
                )
                WHERE ps.property_count IS NOT NULL
                GROUP BY l.name
                HAVING SUM(ps.property_count) > 0
            )
            SELECT 
                location_name,
                'Hyderabad' as city,
                total_property_count,
                avg_price_per_sft,
                min_price_per_sft,
                max_price_per_sft,
                avg_base_price,
                builder_count
            FROM location_property_matches
            ORDER BY avg_price_per_sft DESC;
        """)
        
        rows = cur.fetchall()
        results = []
        
        for row in rows:
            results.append({
                "area_name": row[0],
                "city": row[1],
                "property_count": int(row[2]),
                "avg_price_per_sft": round(float(row[3]), 0),
                "min_price_per_sft": round(float(row[4]), 0),
                "max_price_per_sft": round(float(row[5]), 0),
                "avg_base_price": round(float(row[6]) / 10000000, 2) if row[6] else 0,  # Convert to Crores
                "builder_count": int(row[7]),
                "price_range": f"₹{round(float(row[4]), 0):,} - ₹{round(float(row[5]), 0):,}/sqft"
            })
        
        cur.close()
        conn.close()
        return results
        
    except Exception as e:
        print(f"🔥 PROPERTY COSTS ERROR: {e}")
        return {"error": str(e)}

@app.get("/api/v1/property-costs/{area_name}")
def get_area_property_costs(area_name: str):
    """Get detailed property cost statistics for a specific area from unified_data_DataType_Raghu table"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                %s as search_name,
                'Hyderabad' as city,
                COUNT(*) as property_count,
                AVG(CAST(price_per_sft AS NUMERIC)) as avg_price_per_sft,
                MIN(CAST(price_per_sft AS NUMERIC)) as min_price_per_sft,
                MAX(CAST(price_per_sft AS NUMERIC)) as max_price_per_sft,
                AVG(CAST(baseprojectprice AS NUMERIC)) as avg_base_price,
                MIN(CAST(baseprojectprice AS NUMERIC)) as min_base_price,
                MAX(CAST(baseprojectprice AS NUMERIC)) as max_base_price,
                COUNT(DISTINCT buildername) as builder_count,
                COUNT(DISTINCT projectname) as project_count,
                -- Get top builders in this area
                STRING_AGG(DISTINCT buildername, ', ') as builders
            FROM unified_data_DataType_Raghu 
            WHERE (LOWER(areaname) = LOWER(%s)
                   OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(%s, ' ', ''))
                   OR areaname ILIKE %s
                   OR %s ILIKE areaname)
                AND price_per_sft IS NOT NULL 
                AND price_per_sft != 'None' 
                AND price_per_sft != ''
                AND CAST(price_per_sft AS NUMERIC) > 0
        """, (area_name, area_name, area_name, area_name, area_name))
        
        row = cur.fetchone()
        
        if row:
            # Get sample properties
            cur.execute("""
                SELECT projectname, buildername, price_per_sft, baseprojectprice, bhk
                FROM unified_data_DataType_Raghu 
                WHERE (LOWER(areaname) = LOWER(%s)
                       OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(%s, ' ', ''))
                       OR areaname ILIKE %s
                       OR %s ILIKE areaname)
                    AND price_per_sft IS NOT NULL 
                    AND price_per_sft != 'None' 
                    AND price_per_sft != ''
                ORDER BY CAST(price_per_sft AS NUMERIC) DESC
                LIMIT 5
            """, (area_name, area_name, area_name, area_name))
            
            sample_properties = cur.fetchall()
            
            result = {
                "area_name": row[0],
                "city": row[1],
                "property_count": int(row[2]),
                "avg_price_per_sft": round(float(row[3]), 0),
                "min_price_per_sft": round(float(row[4]), 0),
                "max_price_per_sft": round(float(row[5]), 0),
                "avg_base_price": round(float(row[6]) / 10000000, 2) if row[6] else 0,  # Convert to Crores
                "min_base_price": round(float(row[7]) / 10000000, 2) if row[7] else 0,  # Convert to Crores
                "max_base_price": round(float(row[8]) / 10000000, 2) if row[8] else 0,  # Convert to Crores
                "builder_count": int(row[9]),
                "project_count": int(row[10]),
                "builders": row[11],
                "price_range": f"₹{round(float(row[4]), 0):,} - ₹{round(float(row[5]), 0):,}/sqft",
                "sample_properties": [
                    {
                        "project_name": prop[0],
                        "builder_name": prop[1],
                        "price_per_sft": f"₹{float(prop[2]):,.0f}",
                        "base_price": f"₹{float(prop[3])/10000000:.2f} Cr" if prop[3] and prop[3] != 'None' else "N/A",
                        "bhk": prop[4] if prop[4] and prop[4] != 'None' else "N/A"
                    } for prop in sample_properties
                ]
            }
            
            cur.close()
            conn.close()
            return result
        else:
            return {"error": "Area not found"}
            
    except Exception as e:
        print(f"🔥 AREA PROPERTY COSTS ERROR: {e}")
        return {"error": str(e)}

# ===============================
# AMENITY LOCATIONS (WITH COORDINATES)
# ===============================
# AMENITY LOCATIONS - GOOGLE PLACES API ONLY
# ===============================
@app.get("/api/v1/amenities/{amenity_type}")
def get_amenities(amenity_type: str, lat: float, lng: float):
    """
    Get amenities from Google Places API
    Query params: lat, lng
    amenity_type: 'hospitals', 'schools', 'malls', 'restaurants', 'banks', 'parks', 'metro'
    """
    print(f"🔍 Amenities Request: type={amenity_type}, lat={lat}, lng={lng}")
    
    # Map amenity types to Google Places types
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
    
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type={g_type}&key={api_key}"
    print(f"🌐 Google API URL: {url.replace(api_key, 'API_KEY_HIDDEN')}")

    try:
        print("📡 Making request to Google Places API...")
        r = requests.get(url, timeout=30)
        print(f"📊 Response Status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code} - {r.text}")
            return {"error": f"Google API HTTP {r.status_code}", "amenities": []}

        data = r.json()
        print(f"📋 API Response Status: {data.get('status')}")
        
        if data.get("status") == "REQUEST_DENIED":
            print(f"❌ REQUEST_DENIED - Error: {data.get('error_message', 'No error message')}")
            return {"error": f"Google Places API: {data.get('status')} - {data.get('error_message', 'Check API key and billing')}", "amenities": []}
        
        if data.get("status") != "OK":
            print(f"❌ API Status Error: {data.get('status')} - {data.get('error_message', '')}")
            return {"error": f"Google Places API: {data.get('status')}", "amenities": []}

        results = data.get("results", [])
        print(f"📍 Found {len(results)} raw results from Google")
        
        amenities = []

        # Process results (limit to 15)
        for i, element in enumerate(results[:15]):
            geometry = element.get("geometry", {}).get("location", {})
            amenity_lat = geometry.get("lat")
            amenity_lng = geometry.get("lng")
            
            if not amenity_lat or not amenity_lng:
                print(f"⚠️ Skipping result {i}: missing coordinates")
                continue

            name = element.get("name", f"Unnamed {amenity_type[:-1]}")

            # Calculate distance using Haversine formula (more accurate)
            import math
            R = 6371  # Earth's radius in km
            lat1, lng1 = math.radians(lat), math.radians(lng)
            lat2, lng2 = math.radians(amenity_lat), math.radians(amenity_lng)
            
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
                "latitude": amenity_lat,
                "longitude": amenity_lng,
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
# REAL ESTATE PROJECTS APIs
# ===============================

@app.get("/api/v1/properties")
def get_properties_endpoint(area: str, bhk: str = None):
    """API endpoint to get properties by area with optional BHK filtering"""
    return get_properties_by_area(area, bhk)

def get_properties_by_area(area: str, bhk_filter: str = None):
    """Get real estate projects for a given area name (fuzzy match) from unified_data_DataType_Raghu table - GROUPED BY PROJECT."""
    try:
        conn = get_db()
        cur = conn.cursor()

        # Build the WHERE clause with optional BHK filtering
        where_conditions = [
            """(
                -- Exact match on areaname (case insensitive)
                LOWER(areaname) = LOWER(%s)
                -- Exact match without spaces
                OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(%s, ' ', ''))
                -- areaname starts with search term BUT must end there or be followed by ', '
                -- This prevents 'Appa Junction' matching 'Appa Junction Peerancheru'
                OR LOWER(areaname) LIKE LOWER(%s) || ', %%'
                -- areaname contains search term as whole word (with comma or space boundaries)
                OR LOWER(areaname) LIKE '%%' || LOWER(%s) || ', %%'
                OR LOWER(areaname) LIKE '%%,' || LOWER(%s)
            )"""
        ]

        params = [area, area, area, area, area]

        # Add BHK filter if provided
        if bhk_filter and bhk_filter.strip():
            # Handle both integer and decimal formats (e.g., '2' matches '2.0')
            where_conditions.append("(bhk = %s OR bhk = %s)")
            bhk_val = bhk_filter.strip()
            params.extend([bhk_val, f"{bhk_val}.0"])

        where_clause = " AND ".join(where_conditions)

        # Use strict matching - only exact matches or very close variants
        cur.execute(f"""
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
                rera_number
            FROM unified_data_DataType_Raghu
            WHERE {where_clause}
            ORDER BY
                CASE
                    WHEN LOWER(areaname) = LOWER(%s) THEN 0
                    WHEN LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(%s, ' ', '')) THEN 1
                    WHEN LOWER(areaname) LIKE LOWER(%s) || '%%' THEN 2
                    ELSE 3
                END,
                CAST(COALESCE(NULLIF(google_place_rating, ''), '0') AS NUMERIC) DESC,
                CAST(COALESCE(NULLIF(price_per_sft, ''), '0') AS NUMERIC) DESC
            LIMIT 200;
        """, params + [area, area, area])

        rows = cur.fetchall()
        cur.close()
        conn.close()

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
            "rera_number"
        ]

        # Convert to individual property cards (not grouped by project)
        properties = []
        for r in rows:
            property_data = {}
            for i, col in enumerate(cols):
                val = r[i]
                # Handle numeric conversions safely
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
                property_data[col] = val

            # Create individual property card with all required fields
            property_card = {
                # Card view fields
                'id': property_data.get('id'),
                'projectname': property_data.get('projectname'),
                'buildername': property_data.get('buildername'),
                'project_type': property_data.get('project_type'),
                'bhk': property_data.get('bhk'),
                'sqfeet': property_data.get('sqfeet'),
                'price_per_sft': property_data.get('price_per_sft'),
                'construction_status': property_data.get('construction_status'),
                'areaname': property_data.get('areaname'),
                'images': property_data.get('images'),
                'google_place_location': property_data.get('google_place_location'),


                # Full detail fields for when card is clicked
                'full_details': {
                    # Basic Info
                    'projectname': property_data.get('projectname'),
                    'buildername': property_data.get('buildername'),
                    'project_type': property_data.get('project_type'),
                    'communitytype': property_data.get('communitytype'),
                    'status': property_data.get('status'),
                    'project_status': property_data.get('project_status'),
                    'isavailable': property_data.get('isavailable'),
                    'images': property_data.get('images'),

                    # Location
                    'areaname': property_data.get('areaname'),
                    'projectlocation': property_data.get('projectlocation'),
                    'google_place_name': property_data.get('google_place_name'),
                    'google_place_address': property_data.get('google_place_address'),
                    'google_maps_location': property_data.get('google_maps_location'),
                    'mobile_google_map_url': property_data.get('mobile_google_map_url'),

                    # Pricing
                    'baseprojectprice': property_data.get('baseprojectprice'),
                    'price_per_sft': property_data.get('price_per_sft'),
                    'total_buildup_area': property_data.get('total_buildup_area'),
                    'price_per_sft_update_date': property_data.get('price_per_sft_update_date'),
                    'floor_rise_charges': property_data.get('floor_rise_charges'),
                    'floor_rise_amount_per_floor': property_data.get('floor_rise_amount_per_floor'),
                    'floor_rise_applicable_above_floor_no': property_data.get('floor_rise_applicable_above_floor_no'),
                    'facing_charges': property_data.get('facing_charges'),
                    'preferential_location_charges': property_data.get('preferential_location_charges'),
                    'preferential_location_charges_conditions': property_data.get('preferential_location_charges_conditions'),
                    'amount_for_extra_car_parking': property_data.get('amount_for_extra_car_parking'),

                    # Project Details
                    'project_launch_date': property_data.get('project_launch_date'),
                    'possession_date': property_data.get('possession_date'),
                    'construction_status': property_data.get('construction_status'),
                    'construction_material': property_data.get('construction_material'),
                    'total_land_area': property_data.get('total_land_area'),
                    'number_of_towers': property_data.get('number_of_towers'),
                    'number_of_floors': property_data.get('number_of_floors'),
                    'number_of_flats_per_floor': property_data.get('number_of_flats_per_floor'),
                    'total_number_of_units': property_data.get('total_number_of_units'),
                    'open_space': property_data.get('open_space'),
                    'carpet_area_percentage': property_data.get('carpet_area_percentage'),
                    'floor_to_ceiling_height': property_data.get('floor_to_ceiling_height'),

                    # Unit Configuration
                    'bhk': property_data.get('bhk'),
                    'sqfeet': property_data.get('sqfeet'),
                    'sqyard': property_data.get('sqyard'),
                    'facing': property_data.get('facing'),
                    'no_of_car_parkings': property_data.get('no_of_car_parkings'),

                    # Amenities & Specs
                    'external_amenities': property_data.get('external_amenities'),
                    'specification': property_data.get('specification'),
                    'powerbackup': property_data.get('powerbackup'),
                    'no_of_passenger_lift': property_data.get('no_of_passenger_lift'),
                    'no_of_service_lift': property_data.get('no_of_service_lift'),
                    'visitor_parking': property_data.get('visitor_parking'),
                    'ground_vehicle_movement': property_data.get('ground_vehicle_movement'),
                    'main_door_height': property_data.get('main_door_height'),
                    'home_loan': property_data.get('home_loan'),
                    'available_banks_for_loan': property_data.get('available_banks_for_loan'),

                    # Builder Profile
                    'builder_age': property_data.get('builder_age'),
                    'builder_completed_properties': property_data.get('builder_completed_properties'),
                    'builder_ongoing_projects': property_data.get('builder_ongoing_projects'),
                    'builder_upcoming_properties': property_data.get('builder_upcoming_properties'),
                    'builder_total_properties': property_data.get('builder_total_properties'),
                    'builder_operating_locations': property_data.get('builder_operating_locations'),
                    'builder_origin_city': property_data.get('builder_origin_city'),

                    # Point of Contact
                    'poc_name': property_data.get('poc_name'),
                    'poc_contact': property_data.get('poc_contact'),
                    'poc_role': property_data.get('poc_role'),
                    'alternative_contact': property_data.get('alternative_contact'),
                    'useremail': property_data.get('useremail'),

                    # Additional
                    'google_place_rating': property_data.get('google_place_rating'),
                    'google_place_user_ratings_total': property_data.get('google_place_user_ratings_total'),
                    'rera_number': property_data.get('rera_number')
                }
            }

            properties.append(property_card)

        # Sort by rating (handle None values)
        properties.sort(key=lambda x: x['full_details'].get('google_place_rating') or 0, reverse=True)

        return properties

    except Exception as e:
        print(f"🔥 PROPERTIES ERROR: {e}")
        return {"error": str(e)}
@app.get("/api/v1/properties")
def get_properties_endpoint(area: str, bhk: str = None):
    """API endpoint to get properties by area with optional BHK filtering"""
    return get_properties_by_area(area, bhk)


           


@app.get("/api/v1/properties/{property_id}")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)