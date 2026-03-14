import asyncio
from playwright.async_api import async_playwright
import feedparser
import os
import time
import random
import logging
import re
from datetime import datetime
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIG ---
ARTICLES_PER_LOCATION = 20  # Target articles per location

# Future Development focused queries
FUTURE_DEV_QUERIES = [
    "upcoming projects OR future development OR planned infrastructure",
    "metro expansion OR new metro line OR metro station opening",
    "upcoming mall OR new shopping center OR commercial development",
    "road widening OR flyover construction OR infrastructure project",
    "IT park OR tech hub OR business park development",
    "residential project OR apartment launch OR housing development",
    "hospital expansion OR new medical facility OR healthcare infrastructure",
    "school opening OR educational institution OR university campus",
    "airport expansion OR connectivity improvement OR transport development",
    "smart city project OR GHMC development OR municipal infrastructure"
]

class FutureDevelopmentScraperDB:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        self._ensure_schema()
        logger.info("📁 Connected to database and created future_dev table")

    def _ensure_schema(self):
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS future_dev (
                    id SERIAL PRIMARY KEY,
                    location_id INTEGER,
                    location_name VARCHAR(255),
                    source VARCHAR(255),
                    url TEXT UNIQUE,
                    content TEXT,
                    published_at TIMESTAMP,
                    year_mentioned INTEGER,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT unique_url UNIQUE(url)
                );
            """)
            # Create index for faster queries
            self.cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_future_dev_location_id ON future_dev(location_id);
            """)
            self.cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_future_dev_year ON future_dev(year_mentioned);
            """)
            self.conn.commit()
            logger.info("✅ future_dev table schema ready")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"DB Setup Error: {e}")

    def extract_year_from_content(self, content):
        """Extract year mentions from 2022-2026 range"""
        years = []
        for year in range(2022, 2027):
            if str(year) in content:
                years.append(year)
        return years[0] if years else None

    def insert_article(self, loc_id, location, source, url, content, pub_at, year_mentioned):
        try:
            self.cur.execute("SELECT id FROM future_dev WHERE url = %s", (url,))
            if self.cur.fetchone():
                return False, "duplicate_db"

            self.cur.execute("""
                INSERT INTO future_dev 
                (location_id, location_name, source, url, content, published_at, year_mentioned, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                loc_id, 
                location, 
                source, 
                url, 
                content, 
                pub_at if pub_at else datetime.now(),
                year_mentioned,
                datetime.now()
            ))
            self.conn.commit()
            return True, "success"
        except Exception as e:
            self.conn.rollback()
            logger.error(f"DB Insert Error: {e}")
            return False, f"error: {e}"

    def get_location_count(self, loc_id):
        try:
            self.cur.execute(
                "SELECT COUNT(*) FROM future_dev WHERE location_id = %s",
                (loc_id,)
            )
            return self.cur.fetchone()[0]
        except:
            return 0

    def close(self):
        self.cur.close()
        self.conn.close()
        logger.info("Database connection closed")

    async def fetch_google_news(self, query):
        rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            resp = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            feed = feedparser.parse(resp.content)
            return feed.entries if feed and feed.entries else []
        except:
            return []

    async def process_articles(self, page, feed_entries, loc_id, location, processed_urls, target_count):
        """Process articles until we reach target count"""
        added = 0
        skipped = 0
        
        for entry in feed_entries:
            if added >= target_count:
                break
            
            entry_url = getattr(entry, 'link', None)
            if not entry_url or entry_url in processed_urls:
                skipped += 1
                continue
            
            try:
                await page.goto(entry.link, wait_until="load", timeout=15000)
                if "google.com" in page.url:
                    await page.wait_for_url(lambda u: "google.com" not in u, timeout=8000)
                
                final_url = page.url
                
                if final_url in processed_urls:
                    skipped += 1
                    continue
                
                content_html = await page.content()
                soup = BeautifulSoup(content_html, 'html.parser')
                for s in soup(['script', 'style', 'nav', 'footer', 'header']): 
                    s.decompose()
                text = ' '.join(soup.get_text().split())[:5000]
                
                if len(text) < 500:
                    skipped += 1
                    continue

                # Check if location is mentioned in content
                if location.lower() not in text.lower():
                    skipped += 1
                    continue

                # Extract year mentioned
                year_mentioned = self.extract_year_from_content(text)
                
                source = entry.source.title if hasattr(entry, 'source') else 'News'
                pub_at = entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                success, reason = self.insert_article(loc_id, location, source, final_url, text, pub_at, year_mentioned)
                if success:
                    added += 1
                    processed_urls.add(final_url)
                    year_tag = f" [Year: {year_mentioned}]" if year_mentioned else ""
                    print(f"         ✅ Saved ({added}/{target_count}){year_tag}: {entry.title[:50]}...")
                else:
                    skipped += 1
                
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                skipped += 1
                continue
        
        return added, skipped

    async def run(self, locations_data):
        print(f"🚀 STARTING FUTURE DEVELOPMENT SCRAPER")
        print(f"📅 Target: Articles about future developments (2022-2026)")
        print(f"🎯 Goal: {ARTICLES_PER_LOCATION} articles per location\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()

            for idx, (loc_id, location) in enumerate(locations_data):
                print(f"\n{'='*70}")
                print(f"📍 [{idx+1}/{len(locations_data)}] Processing: {location} (ID: {loc_id})")
                print(f"{'='*70}")
                
                current_count = self.get_location_count(loc_id)
                print(f"   Current records in DB: {current_count}")
                
                if current_count >= ARTICLES_PER_LOCATION:
                    print(f"   ✅ Already has {current_count} articles, skipping...")
                    continue
                
                processed_urls = set()
                location_total = 0
                remaining = ARTICLES_PER_LOCATION - current_count
                
                # Try different query variations
                for query_idx, dev_query in enumerate(FUTURE_DEV_QUERIES, 1):
                    if location_total >= remaining:
                        break
                    
                    print(f"\n   🔍 Query {query_idx}/{len(FUTURE_DEV_QUERIES)}")
                    
                    # Add date range to query
                    full_query = f'{location} Hyderabad ({dev_query}) 2022..2026'
                    entries = await self.fetch_google_news(full_query)
                    
                    if not entries:
                        print(f"      ⚠️ No articles found")
                        continue
                    
                    print(f"      📰 Found {len(entries)} articles")
                    
                    target_for_query = min(5, remaining - location_total)  # Max 5 per query
                    added, skipped = await self.process_articles(
                        page, entries, loc_id, location, processed_urls, target_for_query
                    )
                    location_total += added
                    
                    print(f"      📊 Added: {added}, Skipped: {skipped}")

                    time.sleep(random.uniform(2, 4))
                
                final_count = self.get_location_count(loc_id)
                print(f"\n   📊 Location Summary: {location_total} new articles")
                print(f"   💾 Total in DB: {final_count}")
                print(f"   🎯 Target: {ARTICLES_PER_LOCATION}, Progress: {final_count}/{ARTICLES_PER_LOCATION}")

            await browser.close()
        
        self.close()
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING COMPLETE!")
        print(f"{'='*70}")

if __name__ == "__main__":
    # All Hyderabad locations
    HYDERABAD_LOCATIONS = [
        (37, "Alkapur Main Road"), (66, "Damarigidda"), (177, "Palgutta"), (209, "Patighanpur"), 
        (214, "Peeranchuruvu"), (111, "Podur"), (113, "Appa Junction Peerancheru"), (118, "Depalle"),
        (134, "gourelly"), (77, "Gollur"), (208, "Pati, Kollur"), (149, "Kandawada"), 
        (95, "Krishnareddypet"), (164, "Mansanpally"), (62, "Chegur"), (121, "Sirigiripuram"), 
        (65, "Chiryala"), (41, "Bacharam"), (86, "Gowdavalli"), (192, "Konapur"), (235, "Yamnampet"), 
        (216, "Sainikpuri"), (137, "Uppal Bhagath"), (233, "Velmala"), (213, "Peeramcheruvu"), 
        (161, "Mangalpalli"), (141, "Injapur"), (64, "Chitkul"), (157, "Laxmiguda"), 
        (43, "Bandlaguda-Nagole"), (225, "Toroor"), (71, "Gandi Maisamma"), (70, "Gandamguda"), 
        (146, "Kalyan Nagar"), (94, "Kowkur"), (56, "Budwel"), (232, "Velimela"), (38, "Annojiguda"), 
        (185, "Narapally"), (68, "Dulapally"), (140, "Hastinapuram"), (147, "Kamalanagar"), 
        (39, "Appa Junction"), (184, "Muthangi"), (47, "BEERAMGUDA"), (138, "Guttala Begumpet"), 
        (190, "Khajaguda"), (215, "Puppalguda"), (217, "Rudraram"), (143, "Isnapur"), 
        (159, "Manchirevula"), (228, "Turkapally"), (191, "Kismatpur"), (220, "Shamsheergunj"), 
        (42, "Bahadurpally"), (88, "Gundlapochampally"), (176, "Padmarao Nagar"), (218, "Rampally"), 
        (133, "Gopanpally"), (55, "Bowrampet"), (63, "Chengicherla"), (158, "Mallampet"), 
        (201, "Mansoorabad"), (69, "Gagillapur"), (103, "Moula Ali"), (36, "Adibatla"), 
        (211, "Peerzadiguda"), (67, "Dammaiguda"), (193, "Kongara Kalan"), (180, "Nadergul"), 
        (219, "Raviryal"), (224, "Thumkunta"), (229, "Turkayamjal"), (160, "Mamidipally"), 
        (207, "Patancheruvu"), (150, "Kandlakoya"), (186, "Neknampur"), (131, "Gajularamaram"), 
        (221, "Shadnagar"), (102, "Mokila"), (163, "Manneguda"), (202, "Pocharam"), 
        (139, "Himayat Nagar"), (135, "Habsiguda"), (54, "Bollaram"), (200, "Machirevula"), 
        (44, "Bandlaguda Jagir"), (136, "Hakimpet"), (181, "Nallakunta"), (212, "Saidabad"), 
        (114, "Sanath Nagar"), (154, "Karmanghat"), (155, "Kavadiguda"), (187, "Neopolis"), 
        (59, "Chandanagar"), (120, "Puppalaguda"), (132, "Hafeezpet")
    ]
    
    scraper = FutureDevelopmentScraperDB()
    try:
        asyncio.run(scraper.run(HYDERABAD_LOCATIONS))
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
        scraper.close()
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        scraper.close()
