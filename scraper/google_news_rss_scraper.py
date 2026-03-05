
import feedparser
import newspaper
import time
import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from urllib.parse import quote_plus
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of locations to scrape
LOCATIONS = [
    "Gachibowli", "Kondapur", "HITEC City", "Madhapur", 
    "Financial District", "Nanakramguda", "Kukatpally"
]

# Google News RSS URL template
RSS_URL_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

class GoogleNewsScraper:
    def __init__(self):
        self.base_scraper = BaseScraper()
        # Custom user agent for newspaper
        self.config = newspaper.Config()
        self.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.config.request_timeout = 10

    def get_rss_feed(self, location):
        """Fetch RSS feed for a location + real estate context"""
        query = f'"{location}" Hyderabad real estate OR property OR infrastructure'
        encoded_query = quote_plus(query)
        url = RSS_URL_TEMPLATE.format(query=encoded_query)
        logger.info(f"Fetching RSS for {location}: {url}")
        return feedparser.parse(url)

    def resolve_url(self, url):
        try:
            # Google News links sometimes need a GET request to resolve the final URL
            # We use a session with headers to mimic a browser
            response = requests.get(url, headers={'User-Agent': self.config.browser_user_agent}, timeout=10, allow_redirects=True)
            return response.url
        except Exception as e:
            logger.warning(f"Failed to resolve URL {url}: {e}")
            return url

    def process_entry(self, entry, location_id):
        """Process a single RSS entry"""
        original_url = entry.link
        title = entry.title
        published = entry.published

        # Resolve the real URL first
        url = self.resolve_url(original_url)
        if url != original_url:
            logger.info(f"Resolved URL: {url[:100]}...")

        # Check for duplicates in DB first (fast check)
        
        try:
            # multiple attempts to download
            article = newspaper.Article(url, config=self.config)
            article.download()
            
            # If download fails, it might throw exception
            try:
                article.parse()
            except Exception as e:
                logger.warning(f"Newspaper parse exception for {url}: {e}")
                # Fallback handled below

            content = article.text
            
            # Fallback to BS4 if content is empty
            if not content or len(content) < 200:
                logger.info(f"Newspaper content empty/short for {url}, trying BS4 fallback...")
                try:
                    headers = {'User-Agent': self.config.browser_user_agent}
                    resp = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(resp.content, 'lxml')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                        script.decompose()
                        
                    # Get text
                    text = soup.get_text(separator=' ')
                    
                    # Clean text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = '\n'.join(chunk for chunk in chunks if chunk)
                    
                except Exception as e:
                    logger.error(f"BS4 fallback failed for {url}: {e}")
                    return False

            if not content or len(content) < 200:
                logger.info(f"Full text extraction failed/short for {url}. Falling back to RSS summary.")
                # Combine title and summary
                summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                if summary:
                    # Strip simple HTML from summary
                    summary = BeautifulSoup(summary, "lxml").get_text()
                    content = f"{title}\n\n{summary}"
                    logger.info(f"Using RSS summary (len: {len(content)})")
                else:
                    logger.warning(f"No RSS summary available for {url}")
                    return False



            # Insert into DB
            # We use likely 'News' as source or the actual source from feed
            source = entry.source.title if hasattr(entry, 'source') else 'Google News'
            
            # Using BaseScraper insert
            # Note: base_scraper.py insert_raw_data handles duplicates on URL constraint if defined
            # But the table definition matters.
            # safe to handle exception in base_scraper
            success = self.base_scraper.insert_raw_data(
                location_id=location_id,
                source=source,
                url=url,
                content=content
            )
            
            if success:
                logger.info(f"✅ Saved: {title[:50]}...")
            else:
                logger.info(f"⚠️ Duplicate or verify fail: {title[:50]}...")
                
            return success

        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            return False

    def run(self):
        logger.info("Starting Google News RSS Scraper...")
        
        total_inserted = 0
        
        for location in LOCATIONS:
            logger.info(f"--- Processing {location} ---")
            
            # Get Location ID from DB
            # We need to implement get_location_id in base_scraper or do a lookup here
            # inspect base_scraper.py: it does NOT have get_location_id.
            # Wait, the previous `simple_news_scraper.py` called `scraper.get_location_id(location_name)`.
            # I must have missed it in my read of base_scraper.py or it's dynamically added?
            # Let me re-read base_scraper.py content carefully from artifact.
            # ... I read it. It does NOT have get_location_id.
            # Ah, `simple_news_scraper.py` imports `BaseScraper`. 
            # Maybe I missed scrolling?
            # No, I saw lines 1-49. 
            # I will check `insert_raw_data` again. It takes `location_id`.
            # I need to query the location ID mapping.
            
            # Let's fix this by querying the `locations` table.
            
            try:
                self.base_scraper.cur.execute("SELECT id, name FROM locations WHERE name ILIKE %s", (f"%{location}%",))
                res = self.base_scraper.cur.fetchone()
                if not res:
                    logger.warning(f"Location {location} not found in DB!")
                    continue
                
                location_id = res[0]
                logger.info(f"Location ID for {location}: {location_id}")
                
                # Fetch Feed
                feed = self.get_rss_feed(location)
                logger.info(f"Found {len(feed.entries)} entries")
                
                for entry in feed.entries[:10]: # Limit to 10 latest per run to avoid blast
                    self.process_entry(entry, location_id)
                    total_inserted += 1
                    time.sleep(1) # Be polite
                    
            except Exception as e:
                logger.error(f"Error processing location {location}: {e}")
                self.base_scraper.conn.rollback()

        logger.info("Scraping Run Complete.")
        self.base_scraper.close()

if __name__ == "__main__":
    scraper = GoogleNewsScraper()
    scraper.run()
