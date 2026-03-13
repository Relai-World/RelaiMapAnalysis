
import asyncio
from playwright.async_api import async_playwright
import feedparser
import psycopg2
import os
import sys
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import newspaper
from dotenv import load_dotenv

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# --- CONFIG ---
# --- CONFIG ---
TARGET_PER_THEME_PER_YEAR = 30  # 5 themes * 30 = 150 articles per location/year (Balanced)
YEARS = [2023, 2024, 2025, 2026]

# The "360 Livability" Themes
THEMES = {
    "Real Estate": "real estate OR property prices OR apartments",
    "Infrastructure": "infrastructure OR metro OR flyover OR road widening OR water supply",
    "Safety": "crime OR police OR accident OR theft OR safety",
    "Lifestyle": "mall OR park OR hospital OR school OR restaurant",
    "Corporate": "office opening OR tech park OR jobs OR hiring"
}

LOCATIONS_MAP = {
    "Gachibowli": 1,
    "Kondapur": 4, 
    "HITEC City": 2, 
    "Madhapur": 3,
    "Financial District": 5,
    "Nanakramguda": 6,
    "Kukatpally": 7
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HighEndScraper:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        self.cur = self.conn.cursor()
        self._ensure_schema()
        
    def _ensure_schema(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS news_balanced_corpus_1 (
                id SERIAL PRIMARY KEY,
                location_id INTEGER,
                location_name VARCHAR(100),
                source VARCHAR(200),
                url TEXT UNIQUE,
                content TEXT,
                published_at TIMESTAMP,
                category VARCHAR(50),  -- New column for 'Theme'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Add category column if missing
        try:
            self.cur.execute("ALTER TABLE news_balanced_corpus_1 ADD COLUMN category VARCHAR(50);")
            self.conn.commit()
        except:
            self.conn.rollback()
        self.conn.commit()

    def parse_date(self, entry):
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, 'published'):
            try:
                return parsedate_to_datetime(entry.published)
            except:
                pass
        return datetime.now()

    def extract_content(self, html, url):
        """Use Newspaper3k on rendered HTML"""
        try:
            article = newspaper.Article(url)
            article.set_html(html)
            article.parse()
            text = article.text
            
            if len(text) > 400:
                return text
                
            # Fallback BS4
            soup = BeautifulSoup(html, 'lxml')
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            return "\n\n".join([p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 50])
            
        except Exception:
            return ""

    async def run(self):
        print("🚀 STARTING 360° LIVABILITY SCRAPER (Playwright)")
        print(f"🌍 Themes: {list(THEMES.keys())}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/119.0.0.0 Safari/537.36")
            page = await context.new_page()

            for year in YEARS:
                print(f"\n🗓️  YEAR: {year}")
                
                for location, loc_id in LOCATIONS_MAP.items():
                    print(f"   📍 {location}")
                    
                    for theme_name, theme_query in THEMES.items():
                        # print(f"      👉 Theme: {theme_name}")

                        # Construct: "Gachibowli" Hyderabad (infrastructure OR metro...)
                        full_query = f'"{location}" Hyderabad ({theme_query}) after:{year}-01-01 before:{year}-12-31'
                        rss_url = f"https://news.google.com/rss/search?q={quote_plus(full_query)}&hl=en-IN&gl=IN&ceid=IN:en"
                        
                        feed = feedparser.parse(rss_url)
                        # print(f"      Found {len(feed.entries)} entries for {theme_name}.")
                        
                        success_count = 0
                        for entry in feed.entries:
                            if success_count >= TARGET_PER_THEME_PER_YEAR:
                                break

                            original_url = entry.link
                            
                            try:
                                # Dedupe Check (Fast)
                                # We check if URL exists. If yes, we *could* update the category, but let's just skip for speed.
                                # self.cur.execute("SELECT 1 FROM news_balanced_corpus_1 WHERE url = %s", (url,))
                                # But we can't check URL before resolving Google redirect 100% of time.
                                # However, Google RSS links are unique per article usually.
                                # Let's Resolve First.

                                await page.goto(original_url, wait_until="domcontentloaded", timeout=10000)
                                try:
                                    await page.wait_for_url(lambda u: "google.com" not in u, timeout=5000)
                                except: pass
                                
                                final_url = page.url
                                if "google.com" in final_url: continue

                                # DB Check
                                self.cur.execute("SELECT 1 FROM news_balanced_corpus_1 WHERE url = %s", (final_url,))
                                if self.cur.fetchone():
                                    continue

                                # Content
                                content = await page.content()
                                text = self.extract_content(content, final_url)
                                
                                if len(text) < 300: continue

                                # Save
                                pub_date = self.parse_date(entry)
                                source = entry.source.title if hasattr(entry, 'source') else 'News'
                                
                                self.cur.execute("""
                                    INSERT INTO news_balanced_corpus_1 
                                    (location_id, location_name, source, url, content, published_at, category)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """, (loc_id, location, source, final_url, text, pub_date, theme_name))

                                self.conn.commit()
                                
                                success_count += 1
                                print(f"      ✅ [{theme_name}] Saved: {entry.title[:30]}...")

                            except Exception as e:
                                # print(f"Error: {e}")
                                self.conn.rollback()

            await browser.close()
            self.cur.close()
            self.conn.close()

if __name__ == "__main__":
    scraper = HighEndScraper()
    asyncio.run(scraper.run())
