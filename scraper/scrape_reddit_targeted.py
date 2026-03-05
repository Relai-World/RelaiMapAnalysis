
import asyncio
from playwright.async_api import async_playwright
import psycopg2
import os
import sys
import logging
from datetime import datetime, timedelta
import random

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

# --- CONFIG ---
TARGET_LOCATIONS = {
    "Financial District": 5,
    "Nanakramguda": 6,
    "Gachibowli": 1, # Adding Gachibowli as it often discusses these areas
    "Kukatpally": 7  # Adding Kukatpally as it has less data than others
}

SUBREDDITS = ["hyderabad", "IndiaRealEstate"]
SEARCH_QUERIES = [
    "review", "rent", "traffic", "pollution", "water problem", 
    "apartment", "society", "living in", "cost of living", "metro"
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditScraper:
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
        # We use the same table but will mark Source='Reddit'
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS news_balanced_corpus (
                id SERIAL PRIMARY KEY,
                location_id INTEGER,
                location_name VARCHAR(100),
                source VARCHAR(200),
                url TEXT UNIQUE,
                content TEXT,
                published_at TIMESTAMP,
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    async def run(self):
        print("🚀 STARTING TARGETED REDDIT SCRAPER")
        print(f"🎯 Locations: {list(TARGET_LOCATIONS.keys())}")
        
        async with async_playwright() as p:
            # We use a real user agent to avoid immediate blocking
            browser = await p.chromium.launch(headless=True) # Set headless=False to debug visually
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            for location, loc_id in TARGET_LOCATIONS.items():
                print(f"\n📍 Processing: {location}")
                
                # We search broadly for the location name first
                search_term = f"{location} restricted_sr:on sort:relevance t:all"
                
                for subreddit in SUBREDDITS:
                    search_url = f"https://www.reddit.com/r/{subreddit}/search/?q={location}&restrict_sr=1&sr_nsfw=&sort=relevance&t=all"
                    
                    try:
                        print(f"   🔍 Searching r/{subreddit}...")
                        await page.goto(search_url, timeout=20000)
                        await page.wait_for_timeout(3000) # Let JS load
                        
                        # Scroll to load more
                        for _ in range(3):
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await page.wait_for_timeout(2000)

                        # Extract Post Links
                        # Reddit's structure changes, but usually posts are in <a data-testid="post-title"> or similar
                        # We'll use a generic selector for links containing "/comments/"
                        posts = await page.evaluate('''() => {
                            const links = Array.from(document.querySelectorAll('a[href*="/comments/"]'));
                            return links.map(a => ({
                                title: a.innerText,
                                href: a.href
                            })).filter(l => l.title.length > 10);
                        }''')
                        
                        # Remove duplicates
                        unique_posts = {p['href']: p for p in posts}.values()
                        print(f"      Found {len(unique_posts)} potential discussions.")

                        success_count = 0
                        for post in list(unique_posts)[:20]: # Limit to top 20 relevant per sub per loc
                            url = post['href']
                            title = post['title']
                            
                            # Check DB
                            self.cur.execute("SELECT 1 FROM news_balanced_corpus WHERE url = %s", (url,))
                            if self.cur.fetchone():
                                continue
                                
                            # Visit Post
                            try:
                                await page.goto(url, timeout=15000, wait_until='domcontentloaded')
                                
                                # Extract Body and Top Comments
                                content_data = await page.evaluate('''() => {
                                    // Get main post content
                                    const body = document.querySelector('[data-test-id="post-content"]');
                                    const bodyText = body ? body.innerText : "";
                                    
                                    // Get top comments (limit 5)
                                    const comments = Array.from(document.querySelectorAll('.Comment')).slice(0, 5);
                                    const commentText = comments.map(c => c.innerText).join("\\n---\\n");
                                    
                                    return bodyText + "\\n\\n--- TOP COMMENTS ---\\n" + commentText;
                                }''')
                                
                                full_content = f"TITLE: {title}\n\n{content_data}"
                                
                                if len(full_content) < 100: continue

                                # Approximate Date (Reddit makes this hard without API)
                                pub_date = datetime.now() # Default to now as "witnessed at"
                                
                                # Insert
                                self.cur.execute("""
                                    INSERT INTO news_balanced_corpus 
                                    (location_id, location_name, source, url, content, published_at, category)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """, (loc_id, location, 'Reddit', url, full_content, pub_date, 'Community Review'))
                                self.conn.commit()
                                
                                success_count += 1
                                print(f"      ✅ Saved: {title[:40]}...")
                                await page.wait_for_timeout(1000) # Polite delay
                                
                            except Exception as e:
                                # logger.error(f"Failed post {url}: {e}")
                                pass

                    except Exception as e:
                        print(f"   ❌ Error searching r/{subreddit}: {e}")

            await browser.close()
            self.cur.close()
            self.conn.close()

if __name__ == "__main__":
    scraper = RedditScraper()
    asyncio.run(scraper.run())
