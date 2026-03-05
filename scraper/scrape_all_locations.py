
import asyncio
from playwright.async_api import async_playwright
import feedparser
import psycopg2
import os
import sys
import logging
import argparse
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# --- CONFIG ---
TARGET_PER_THEME_PER_YEAR = 10 
YEARS = [2021, 2022, 2023, 2024, 2025, 2026] 

# The "360 Livability" Themes (Original)
THEMES = {
    "Real Estate": "real estate OR property prices OR apartments OR new launches",
    "Infrastructure": "infrastructure OR metro OR flyover OR road widening OR water supply",
    "Safety": "crime OR police OR accident OR theft OR safety",
    "Lifestyle": "mall OR park OR hospital OR school OR restaurant",
    "Corporate": "office opening OR tech park OR jobs OR hiring"
}

# Mapping of common Hyderabad spelling variations / aliases
ALIASES = {
    "Kajaguda": ["Khajaguda"],
    "Khajaguda": ["Kajaguda"],
    "BEERAMGUDA": ["Beeramguda", "Bheeramguda"],
    "Tellapur": ["Telapur"],
    "Kollur": ["Kolur"],
    "Narsingi": ["Narasingi"],
    "Kokapet": ["Kokapeta"],
    "Manikonda": ["Manykonda"],
    "Patancheru": ["Patanchur", "Patancherry"],
    "Adibatla": ["Adi Batla"],
    "Appa Junction": ["Appa Jn", "APPA Junction Peerancheru"],
    "Mokila": ["Mokila Village"],
    "Financial District": ["Nanakramguda", "ISB Road"],
    "Puppalaguda": ["Puppalguda"],
    "Bachupally": ["Bachupalli"],
    "Yousufguda": ["Yousuf Guda", "Yusufguda"],
    "Gachibowli": ["Gachbowli"],
    "Ameerpet": ["Amirpet"],
    "Miyapur": ["Myapur"],
    "Kothaguda": ["Kotaguda"],
    "Kondapur": ["Kondapura"],
    "Madhapur": ["Madapur"],
    "Hitech City": ["HITEC City", "HITEX"],
    "Gandipet": ["Gandipeta"],
    "Osman Nagar": ["Osmannagar"],
    "Nallagandla": ["Nallagandla Village"],
    "Kismatpur": ["Kismatpura"],
    "Banjara Hills": ["Banjara"],
    "Jubilee Hills": ["Jubilee"],
    "LB Nagar": ["L.B. Nagar", "Lal Bahadur Nagar"]
}

class UniversalHyderabadScraper:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        self.cur = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS news_balanced_corpus (
                    id SERIAL PRIMARY KEY,
                    location_id INTEGER,
                    location_name VARCHAR(255),
                    source VARCHAR(255),
                    url TEXT UNIQUE,
                    content TEXT,
                    published_at TIMESTAMP,
                    category VARCHAR(100),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"DB Setup Error: {e}")

    def get_locations_batch(self, limit=30, offset=0):
        """Fetch a batch of Hyderabad locations from DB"""
        self.cur.execute("""
            SELECT id, name FROM locations 
            WHERE ST_Y(geom) BETWEEN 17.0 AND 18.0 
            AND ST_X(geom) BETWEEN 78.0 AND 79.0
            ORDER BY id ASC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return self.cur.fetchall()

    def parse_date(self, entry):
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        return datetime(2024, 1, 1)

    def extract_content(self, html_content, url):
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except:
            soup = BeautifulSoup(html_content, 'html.parser')
            
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        text = ' '.join(soup.get_text().split())
        return text[:5000]

    def generate_variants(self, name):
        """Generates common variations of Indian location names"""
        variants = {f'"{name}"'}
        
        # 1. Manual Aliases (Highest Priority)
        if name in ALIASES:
            for a in ALIASES[name]:
                variants.add(f'"{a}"')
        
        # 2. Add/Remove 'h' (Only for middle-word digraphs like th, dh, kh)
        # These are common transliteration variations in Telugu/Hindi
        name_lower = name.lower()
        if 'th' in name_lower:
            variants.add(f'"{name_lower.replace("th", "t").title()}"')
        if 'dh' in name_lower:
            variants.add(f'"{name_lower.replace("dh", "d").title()}"')
        if 'kh' in name_lower:
            variants.add(f'"{name_lower.replace("kh", "k").title()}"')
            
        # Specific known swap: Kajaguda <-> Khajaguda
        if name_lower == "kajaguda":
            variants.add('"Khajaguda"')
        elif name_lower == "khajaguda":
            variants.add('"Kajaguda"')

        # 3. 'i' vs 'y' at the end (e.g. Manikonda / Manykonda, Bachupally / Bachupalli)
        if name.endswith('i'):
            variants.add(f'"{name[:-1]}y"')
        elif name.endswith('y'):
            variants.add(f'"{name[:-1]}i"')
            
        return list(variants)

    async def run(self, limit=30, offset=0):
        import time
        import random
        
        locations = self.get_locations_batch(limit, offset)
        if not locations:
            print("No locations found.")
            return

        print(f"🚀 STARTING UNIVERSAL HYDERABAD SCRAPER (Batch: {limit} locations, Offset: {offset})")
        print(f"🌍 Found {len(locations)} locations to process.")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            for idx, (loc_id, location) in enumerate(locations):
                print(f"\n📍 [{idx+1}/{len(locations)}] Processing: {location} (ID: {loc_id})")
                
                variants = self.generate_variants(location)
                location_query = f"({' OR '.join(variants)})"
                
                # BUCKET STRATEGY: 2 Requests per Theme (Deep History + Current)
                # This ensures we get old data (2021-23) AND new data (2024-26) 
                # while keeping traffic 66% lower than the original year-by-year approach.
                BUCKETS = [
                    ("Historical", "2021-01-01", "2023-12-31"),
                    ("Recent", "2024-01-01", "2026-12-31")
                ]

                for theme_name, theme_query in THEMES.items():
                    for bucket_label, start_date, end_date in BUCKETS:
                        full_query = f'{location_query} Hyderabad ({theme_query}) after:{start_date} before:{end_date}'
                        rss_url = f"https://news.google.com/rss/search?q={quote_plus(full_query)}&hl=en-IN&gl=IN&ceid=IN:en"
                        
                        # --- RSS Fetch with Browser Headers + Retries ---
                        max_retries = 3
                        feed = None
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Referer': 'https://news.google.com/'
                        }

                        for attempt in range(max_retries):
                            try:
                                # Fetch using requests first (better headers than feedparser's default)
                                resp = requests.get(rss_url, headers=headers, timeout=20)
                                if resp.status_code == 503:
                                    wait_time = (attempt + 1) * 120 # Wait 2, 4, 6 minutes
                                    print(f"      ⚠️ Rate Limited (503). Bucket: {bucket_label}. Waiting {wait_time}s...")
                                    time.sleep(wait_time)
                                    continue
                                
                                feed = feedparser.parse(resp.content)
                                break
                            except Exception as re:
                                print(f"      ⚠️ Request Error: {re}. Retrying...")
                                time.sleep(5)
                        
                        if not feed or not feed.entries:
                            time.sleep(random.uniform(3, 6))
                            continue
                            
                        print(f"      📡 Theme: {theme_name} ({bucket_label}) | Found {len(feed.entries)} entries")
                        
                        success_count = 0
                        for entry in feed.entries:
                            # Target 30 per bucket = 60 total per theme
                            if success_count >= (TARGET_PER_THEME_PER_YEAR * 3): 
                                break

                            original_url = entry.link
                            try:
                                # URL Dupe Check
                                self.cur.execute("SELECT 1 FROM news_balanced_corpus WHERE url = %s", (original_url,))
                                if self.cur.fetchone(): continue

                                await page.goto(original_url, wait_until="load", timeout=15000)
                                if "google.com" in page.url:
                                    await page.wait_for_url(lambda u: "google.com" not in u, timeout=8000)
                                
                                final_url = page.url
                                if "google.com" in final_url: continue

                                self.cur.execute("SELECT 1 FROM news_balanced_corpus WHERE url = %s", (final_url,))
                                if self.cur.fetchone(): continue

                                content = await page.content()
                                text = self.extract_content(content, final_url)
                                if len(text) < 300: continue

                                pub_date = self.parse_date(entry)
                                source = entry.source.title if hasattr(entry, 'source') else 'News'
                                
                                self.cur.execute("""
                                    INSERT INTO news_balanced_corpus 
                                    (location_id, location_name, source, url, content, published_at, category)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """, (loc_id, location, source, final_url, text, pub_date, theme_name))
                                self.conn.commit()
                                
                                success_count += 1
                                print(f"      ✅ Saved: {entry.title[:50]}...")
                                time.sleep(random.uniform(1, 2))

                            except Exception:
                                self.conn.rollback()

                        # Delay between buckets
                        time.sleep(random.uniform(4, 7))

            await browser.close()
            self.cur.close()
            self.conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    scraper = UniversalHyderabadScraper()
    asyncio.run(scraper.run(limit=args.limit, offset=args.offset))
