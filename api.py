from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   
import psycopg2
import requests
import time

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Real Estate Intelligence API")

# Health Check Endpoint (Recommended for Render)
@app.get("/")
def health_check():
    return {"status": "ok", "message": "West Hyderabad Intelligence API is running"}

# ===============================
# STATIC FILES REMOVED
# ===============================
# We are separating Frontend (GitHub Pages) and Backend (Render).
# The backend will ONLY serve API JSON data now.
# app.mount("/static", StaticFiles(directory="frontend"), name="static")

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
    # Priority 1: Use full connection URI (Most reliable for Render + Supabase)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    
    # Priority 2: Individual variables (Fallback)
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "6543") # Default to pooler port
    )

# ===============================
# CORE INSIGHTS (UNCHANGED)
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
                li.investment_score
            FROM locations l
            JOIN location_insights li
              ON li.location_id = l.id
            ORDER BY l.name;
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "location_id": r[0],
                "location": r[1],
                "longitude": float(r[2]),
                "latitude": float(r[3]),
                "avg_sentiment": float(r[4]),
                "growth_score": float(r[5]),
                "investment_score": float(r[6])
            }
            for r in rows
        ]
    except Exception as e:
        print(f"🔥 DATABASE ERROR: {e}")
        return {"error": str(e), "message": "Failed to connect to database or fetch insights"}

# ===============================
# SAFE OVERPASS COUNT (UNCHANGED)
# ===============================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def safe_count(query: str) -> int:
    try:
        r = requests.post(
            OVERPASS_URL,
            data=query,
            timeout=20,
            headers={"Accept": "application/json"}
        )

        if r.status_code != 200:
            return 0

        data = r.json()
        return len(data.get("elements", []))

    except Exception:
        return 0

# ===============================
# LOCATION INFRA COUNTS (UNCHANGED)
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
        return {
            "hospitals": 0,
            "schools": 0,
            "metro": 0,
            "airports": 0
        }

    lat, lng = row

    base = f"""
    [out:json][timeout:25];
    (
      node(around:3000,{lat},{lng})[{0}];
      way(around:3000,{lat},{lng})[{0}];
    );
    out body;
    """

    time.sleep(1)

    return {
        "hospitals": safe_count(base.format("amenity=hospital")),
        "schools": safe_count(base.format("amenity=school")),
        "metro": safe_count(base.format("railway=station")),
        "airports": safe_count(base.format("aeroway=aerodrome"))
    }
