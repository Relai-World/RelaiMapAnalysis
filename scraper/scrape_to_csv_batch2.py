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
ARTICLES_PER_THEME = 15

# Expanded themes - 12 themes total
THEMES = {
    "Real Estate": "property prices OR apartments OR housing OR flats OR villas OR plots OR land rates OR builders",
    "Infrastructure": "metro rail OR flyover OR road widening OR water supply OR ORR OR RRR OR HMDA OR GHMC",
    "Safety": "police OR crime OR accident OR theft OR safety OR law order OR security OR FIR OR investigation",
    "Lifestyle": "mall OR shopping OR hospital OR school OR restaurant OR cinema OR theater OR gym OR healthcare",
    "Corporate": "IT park OR tech company OR jobs OR hiring OR business OR startup OR investment OR economy",
    "Government": "CM OR minister OR election OR municipal OR corporation OR development authority OR smart city",
    "Transport": "airport OR metro station OR bus OR connectivity OR traffic OR railway OR logistics",
    "Environment": "pollution OR green OR trees OR park OR lake OR environment OR climate OR weather OR nature",
    "Education": "school OR college OR university OR education OR student OR exam OR results OR campus OR academic",
    "Health": "hospital OR health OR medical OR doctor OR patient OR disease OR treatment OR vaccine OR healthcare",
    "Sports": "sports OR cricket OR stadium OR match OR tournament OR player OR game OR fitness OR yoga",
    "Entertainment": "movie OR film OR cinema OR actor OR actress OR concert OR event OR celebration OR festival"
}

ALIASES = {}

class PortableScraperDB:
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
        logger.info("📁 Connected to database")

    def _ensure_schema(self):
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

    def generate_variants(self, name):
        variants = {name}
        if name in ALIASES:
            for alias in ALIASES[name]:
                variants.add(alias)
        return list(variants)

    def extract_location_from_content(self, content, location_variants):
        """Extract exact location mentions from article content"""
        content_lower = content.lower()
        found_locations = []
        
        for variant in location_variants:
            if variant.lower() in content_lower:
                found_locations.append(variant)
        
        return found_locations

    def insert_article(self, loc_id, location, source, url, content, pub_at, category, extracted_locations):
        try:
            self.cur.execute("SELECT id FROM news_balanced_corpus WHERE url = %s", (url,))
            if self.cur.fetchone():
                return False, "duplicate_db"

            location_tag = f"[LOCATIONS: {', '.join(extracted_locations)}] " if extracted_locations else ""
            tagged_content = location_tag + content

            self.cur.execute("""
                INSERT INTO news_balanced_corpus 
                (location_id, location_name, source, url, content, published_at, category, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                loc_id, 
                location, 
                source, 
                url, 
                tagged_content, 
                pub_at if pub_at else datetime.now(),
                category,
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
                "SELECT COUNT(*) FROM news_balanced_corpus WHERE location_id = %s",
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

    async def process_theme_articles(self, page, feed_entries, loc_id, location, category, 
                                     processed_urls, location_variants):
        """Process exactly ARTICLES_PER_THEME articles for a theme"""
        added = 0
        skipped = 0
        
        for entry in feed_entries:
            if added >= ARTICLES_PER_THEME:
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

                extracted_locations = self.extract_location_from_content(text, location_variants)
                
                source = entry.source.title if hasattr(entry, 'source') else 'News'
                pub_at = entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                success, reason = self.insert_article(loc_id, location, source, final_url, text, pub_at, category, extracted_locations)
                if success:
                    added += 1
                    processed_urls.add(final_url)
                    loc_indicator = f" [Locs: {len(extracted_locations)}]" if extracted_locations else ""
                    print(f"         ✅ Saved ({added}/{ARTICLES_PER_THEME}){loc_indicator}: {entry.title[:40]}...")
                else:
                    skipped += 1
                
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                skipped += 1
                continue
        
        return added, skipped

    async def run(self, locations_data):
        total_themes = len(THEMES)
        expected_per_location = ARTICLES_PER_THEME * total_themes
        
        print(f"🚀 STARTING SCRAPER - {ARTICLES_PER_THEME} articles per theme × {total_themes} themes = {expected_per_location} per location")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()

            for idx, (loc_id, location) in enumerate(locations_data):
                print(f"\n{'='*60}")
                print(f"📍 [{idx+1}/{len(locations_data)}] Processing: {location} (ID: {loc_id})")
                print(f"{'='*60}")
                
                location_variants = self.generate_variants(location)
                location_query = f"({' OR '.join(location_variants)})"
                
                current_count = self.get_location_count(loc_id)
                print(f"   Current records in DB: {current_count}")
                
                processed_urls = set()
                location_total = 0
                
                for theme_idx, (theme_name, theme_query) in enumerate(THEMES.items(), 1):
                    print(f"\n   🏷️ [{theme_idx}/{total_themes}] Theme: {theme_name}")
                    
                    full_query = f'{location_query} Hyderabad ({theme_query})'
                    entries = await self.fetch_google_news(full_query)
                    
                    if not entries:
                        print(f"      ⚠️ No articles found")
                        continue
                    
                    print(f"      📰 Found {len(entries)} articles, taking max {ARTICLES_PER_THEME}")
                    
                    added, skipped = await self.process_theme_articles(
                        page, entries, loc_id, location, theme_name,
                        processed_urls, location_variants
                    )
                    location_total += added
                    
                    status = "✅ Complete" if added >= ARTICLES_PER_THEME else f"⚠️ Only {added}"
                    print(f"      📊 {status} (skipped: {skipped})")

                    time.sleep(random.uniform(2, 4))
                
                final_count = self.get_location_count(loc_id)
                print(f"\n   📊 Location Summary: {location_total} new, {final_count} total in DB")
                print(f"   🎯 Expected: {expected_per_location}, Got: {location_total}")

            await browser.close()
        
        self.close()

if __name__ == "__main__":
    # Start from Shamirpet (ID: 217)
    LOCS_TO_SCRAPE = [
        
       (37, "Alkapur Main Road"), (66, "Damarigidda"), (177, "Palgutta"), (209, "Patighanpur"), (214, "Peeranchuruvu"),
            (111, "Podur"), (113, "Appa Junction Peerancheru"), (118, "Depalle"), (134, "gourelly"), (77, "Gollur"),
            (208, "Pati, Kollur"), (149, "Kandawada"), (95, "Krishnareddypet"), (164, "Mansanpally"), (62, "Chegur"),
            (121, "Sirigiripuram"), (65, "Chiryala"), (41, "Bacharam"), (86, "Gowdavalli"), (192, "Konapur"),
            (235, "Yamnampet"), (216, "Sainikpuri"), (137, "Uppal Bhagath"), (233, "Velmala"), (213, "Peeramcheruvu"),
            (161, "Mangalpalli"), (141, "Injapur"), (64, "Chitkul"), (157, "Laxmiguda"), (43, "Bandlaguda-Nagole"),
            (225, "Toroor"), (71, "Gandi Maisamma"), (70, "Gandamguda"), (146, "Kalyan Nagar"), (94, "Kowkur"),
            (56, "Budwel"), (232, "Velimela"), (38, "Annojiguda"), (185, "Narapally"), (68, "Dulapally"),
            (140, "Hastinapuram"), (147, "Kamalanagar"), (39, "Appa Junction"), (184, "Muthangi"), (47, "BEERAMGUDA"),
            (138, "Guttala Begumpet"), (190, "Khajaguda"), (215, "Puppalguda"), (217, "Rudraram"), (143, "Isnapur"),
            (159, "Manchirevula"), (228, "Turkapally"), (191, "Kismatpur"), (220, "Shamsheergunj"), (42, "Bahadurpally"),
            (88, "Gundlapochampally"), (176, "Padmarao Nagar"), (218, "Rampally"), (133, "Gopanpally"), (55, "Bowrampet"),
            (63, "Chengicherla"), (158, "Mallampet"), (201, "Mansoorabad"), (69, "Gagillapur"), (103, "Moula Ali"),
            (36, "Adibatla"), (211, "Peerzadiguda"), (67, "Dammaiguda"), (193, "Kongara Kalan"), (180, "Nadergul"),
            (219, "Raviryal"), (224, "Thumkunta"), (229, "Turkayamjal"), (160, "Mamidipally"), (207, "Patancheruvu"),
            (150, "Kandlakoya"), (186, "Neknampur"), (131, "Gajularamaram"), (221, "Shadnagar"), (102, "Mokila"),
            (163, "Manneguda"), (202, "Pocharam"), (139, "Himayat Nagar"), (135, "Habsiguda"), (54, "Bollaram"),
            (200, "Machirevula"), (44, "Bandlaguda Jagir"), (136, "Hakimpet"), (181, "Nallakunta"), (212, "Saidabad"),
            (114, "Sanath Nagar"), (154, "Karmanghat"), (155, "Kavadiguda"), (187, "Neopolis"), (59, "Chandanagar"),
            (120, "Puppalaguda"), (132, "Hafeezpet")
    ]
    
    scraper = PortableScraperDB()
    try:
        asyncio.run(scraper.run(LOCS_TO_SCRAPE))
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
        scraper.close()
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        scraper.close()