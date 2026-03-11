"""
IGRS Scraper - Database-Driven with Playwright
Fetches all locations from database and scrapes IGRS data
"""

import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import psycopg2
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from pathlib import Path
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('igrs_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -----------------------------
# CONFIGURATION
# -----------------------------

DISTRICT = "RANGAREDDY"
MANDAL = "Serilingampally"

# Date ranges (2019-2026, yearly for faster scraping)
DATE_RANGES = [
    ("01-01-2019", "31-12-2019", "2019"),
    ("01-01-2020", "31-12-2020", "2020"),
    ("01-01-2021", "31-12-2021", "2021"),
    ("01-01-2022", "31-12-2022", "2022"),
    ("01-01-2023", "31-12-2023", "2023"),
    ("01-01-2024", "31-12-2024", "2024"),
    ("01-01-2025", "31-12-2025", "2025"),
    ("01-01-2026", "31-12-2026", "2026"),
]

# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_locations_from_db():
    """Fetch all Hyderabad locations from database"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        query = """
            SELECT name
            FROM locations
            WHERE city = 'Hyderabad'
            ORDER BY name
        """
        
        cur.execute(query)
        locations = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        logger.info(f"✅ Fetched {len(locations)} locations from database")
        return locations
        
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return []

# -----------------------------
# PROGRESS TRACKING
# -----------------------------

PROGRESS_FILE = "scraping_progress.json"

def load_progress():
    """Load scraping progress"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            data['completed'] = set(data.get('completed', []))
            return data
    return {
        'completed': set(),
        'failed': [],
        'stats': {'total_records': 0, 'locations_completed': 0}
    }

def save_progress(progress):
    """Save scraping progress"""
    progress_copy = progress.copy()
    progress_copy['completed'] = list(progress['completed'])
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress_copy, f, indent=2)
