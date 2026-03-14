"""
Future Development Theme Scraper
=================================
Scrapes news articles about future development projects, upcoming infrastructure,
planned amenities, and growth initiatives for all Hyderabad locations.

Themes Covered:
- Future Infrastructure Projects (Metro expansions, flyovers, roads)
- Upcoming Commercial Developments (IT parks, malls, townships)
- Planned Public Amenities (Schools, hospitals, parks)
- Government Development Initiatives (HMDA, GHMC projects)
- Real Estate Future Projects (New launches, townships)
- Transportation Future Plans (Airport expansion, bus terminals)
"""

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
from dotenv import load_dotenv

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# --- CONFIG ---
TARGET_PER_THEME_PER_YEAR = 15  # Articles per theme per location per year
YEARS = [2023, 2024, 2025, 2026]  # Recent years for future planning info

# Future Development Themes
THEMES = {
    "Future Infrastructure": "future metro OR upcoming flyover OR proposed road OR planned infrastructure OR future development",
    "Upcoming Projects": "new IT park OR upcoming mall OR proposed township OR new hospital OR upcoming school OR future project",
    "Government Plans": "HMDA master plan OR GHMC development OR proposed budget OR future scheme OR government project",
    "Real Estate Future": "upcoming launch OR new residential OR future commercial OR proposed layout OR pre-launch",
    "Transportation Future": "airport expansion OR new metro line OR proposed bus terminal OR future connectivity OR RRR phase",
    "Smart City": "smart city OR technology park OR innovation district OR digital hub OR future tech"
}

# All Hyderabad Locations from Database
LOCATIONS_QUERY = """
    SELECT id, name 
    FROM locations 
    WHERE city ILIKE '%Hyderabad%' OR city IS NULL
    ORDER BY name
"""

# Database Configuration
DB_NAME = os.getenv("DB_NAME", "real_estate_intelligence")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "post@123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FutureDevelopmentScraper:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        self.cur = self.conn.cursor()
        
    def get_locations(self):
        """Fetch all Hyderabad locations from database"""
        self.cur.execute(LOCATIONS_QUERY)
        return self.cur.fetchall()
    
    def is_duplicate(self, url):
        """Check if URL already exists in database"""
        self.cur.execute("SELECT 1 FROM news_balanced_corpus WHERE url = %s", (url,))
        return self.cur.fetchone() is not None
    
    def insert_article(self, location_id, theme_name, source, url, content, pub_date):
        """Insert article into database"""
        try:
            self.cur.execute("""
                INSERT INTO news_balanced_corpus 
                (location_id, category, source, url, content, published_at, scraped_at, sentiment_label)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                location_id,
                theme_name,
                source,
                url,
                content[:5000],  # Limit content length
                pub_date,
                datetime.now(),
                'neutral'  # Will be classified later by sentiment analysis
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            self.conn.rollback()
            return False
    
    def extract_content_from_html(self, html_content, url):
        """Extract main content from HTML using BeautifulSoup"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script, style, nav, footer
        for s in soup(['script', 'style', 'nav', 'footer', 'header']):
            s.decompose()
        
        # Get text
        text = ' '.join(soup.get_text().split())
        
        # Clean up
        text = text[:5000]  # Limit length
        return text if len(text) > 200 else None
    
    async def scrape_google_news(self, page, location_name, location_id, theme_name, theme_query, year):
        """Scrape Google News RSS for specific location, theme, and year"""
        # Construct query: "Location Name" Hyderabad (theme keywords) after:YEAR-01-01 before:YEAR-12-31
        full_query = f'"{location_name}" Hyderabad ({theme_query}) after:{year}-01-01 before:{year}-12-31'
        rss_url = f"https://news.google.com/rss/search?q={quote_plus(full_query)}&hl=en-IN&gl=IN&ceid=IN:en"
        
        try:
            feed = feedparser.parse(rss_url)
            success_count = 0
            
            for entry in feed.entries:
                if success_count >= TARGET_PER_THEME_PER_YEAR:
                    break
                
                original_url = entry.link
                
                try:
                    # Navigate to article (bypass Google redirect)
                    await page.goto(original_url, wait_until="domcontentloaded", timeout=10000)
                    
                    # Wait for redirect to finish
                    try:
                        await page.wait_for_url(lambda u: "google.com" not in u, timeout=5000)
                    except:
                        pass
                    
                    final_url = page.url
                    
                    # Skip if still on Google
                    if "google.com" in final_url:
                        continue
                    
                    # Check duplicate
                    if self.is_duplicate(final_url):
                        continue
                    
                    # Extract content
                    html_content = await page.content()
                    content = self.extract_content_from_html(html_content, final_url)
                    
                    if not content or len(content) < 300:
                        continue
                    
                    # Parse publication date
                    pub_date = datetime.now()
                    if hasattr(entry, 'published'):
                        try:
                            pub_date = parsedate_to_datetime(entry.published)
                        except:
                            pass
                    
                    # Get source
                    source = entry.source.title if hasattr(entry, 'source') else 'Google News'
                    
                    # Insert to database
                    if self.insert_article(location_id, theme_name, source, final_url, content, pub_date):
                        success_count += 1
                        logger.info(f"✅ [{location_name}] {theme_name}: {entry.title[:60]}...")
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.debug(f"Failed to process article: {e}")
                    continue
            
            return success_count
            
        except Exception as e:
            logger.error(f"Error scraping Google News: {e}")
            return 0
    
    async def run(self):
        """Main scraping execution"""
        logger.info("🚀 FUTURE DEVELOPMENT SCRAPER STARTED")
        logger.info(f"📊 Targeting {len(THEMES)} themes across {len(YEARS)} years")
        
        locations = self.get_locations()
        logger.info(f"📍 Found {len(locations)} Hyderabad locations")
        
        total_inserted = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            for loc_id, location_name in locations:
                logger.info(f"\n{'='*80}")
                logger.info(f"📍 SCRAPING LOCATION: {location_name} (ID: {loc_id})")
                
                for theme_name, theme_query in THEMES.items():
                    logger.info(f"\n   👉 THEME: {theme_name}")
                    
                    yearly_total = 0
                    
                    for year in YEARS:
                        logger.info(f"      📅 Year: {year}")
                        
                        count = await self.scrape_google_news(
                            page, 
                            location_name, 
                            loc_id, 
                            theme_name, 
                            theme_query, 
                            year
                        )
                        
                        yearly_total += count
                        logger.info(f"         ✅ Articles found: {count}")
                        
                        # Delay between years
                        await asyncio.sleep(random.uniform(3, 5))
                    
                    logger.info(f"   📊 Total for {theme_name}: {yearly_total} articles")
                    total_inserted += yearly_total
                    
                    # Delay between themes
                    await asyncio.sleep(random.uniform(5, 8))
                
                logger.info(f"\n✅ COMPLETED: {location_name} - Total: {total_inserted} articles")
                
                # Longer delay between locations
                await asyncio.sleep(random.uniform(10, 15))
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        
        logger.info(f"\n{'='*80}")
        logger.info("✅ FUTURE DEVELOPMENT SCRAPING COMPLETE")
        logger.info(f"📊 TOTAL ARTICLES INSERTED: {total_inserted}")
        logger.info(f"📈 Average per location: {total_inserted // len(locations) if locations else 0}")


if __name__ == "__main__":
    import random
    
    try:
        scraper = FutureDevelopmentScraper()
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
