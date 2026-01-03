import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, urljoin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from base_scraper import BaseScraper
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import hashlib

# =========================================================
# LOGGING SETUP
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================
@dataclass
class ScraperConfig:
    """Centralized configuration"""
    headers: Dict[str, str] = None
    request_delay: float = 2.5
    article_delay: float = 1.5
    min_article_length: int = 600
    max_retries: int = 3
    timeout: int = 15
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }

CONFIG = ScraperConfig()

# =========================================================
# LOCATION DATA
# =========================================================
WEST_HYD_LOCATIONS = {
    "Gachibowli": {
        "aliases": ["gachibowli", "gachi bowli"],
        "priority": 1
    },
    "Kondapur": {
        "aliases": ["kondapur", "konda pur"],
        "priority": 1
    },
    "HITEC City": {
        "aliases": ["hitec city", "hi-tech city", "hitech city", "hitec"],
        "priority": 1
    },
    "Madhapur": {
        "aliases": ["madhapur", "madha pur"],
        "priority": 1
    },
    "Financial District": {
        "aliases": ["financial district", "neopolis", "fd hyderabad"],
        "priority": 1
    },
    "Nanakramguda": {
        "aliases": ["nanakramguda", "nanakram guda"],
        "priority": 2
    },
    "Kukatpally": {
        "aliases": ["kukatpally", "kphb", "kphb colony", "kukkatpally"],
        "priority": 2
    }
}

# =========================================================
# KEYWORD GROUPS
# =========================================================
KEYWORD_GROUPS = {
    "real_estate": ["real estate", "property", "housing", "residential", "apartments", "villas"],
    "commercial": ["commercial", "office space", "it park", "tech park", "business park"],
    "infrastructure": ["metro", "metro rail", "road", "flyover", "bridge", "corridor", "outer ring road"],
    "development": ["investment", "construction", "development", "project", "launch", "growth"]
}

# Flatten for quick checks
ALL_KEYWORDS = [kw for group in KEYWORD_GROUPS.values() for kw in group]

# =========================================================
# EXCLUSION PATTERNS
# =========================================================
EXCLUDE_PATTERNS = [
    r"\bmumbai\b", r"\bdelhi\b", r"\bbengaluru\b", r"\bbangalore\b",
    r"\bchennai\b", r"\bkolkata\b", r"\bpune\b",
    r"\bnationwide\b", r"\ball india\b", r"\bacross india\b",
    r"\belection\b", r"\bparliament\b", r"\bunion budget\b",
    r"\bcricket\b", r"\bfilm\b", r"\bmovie\b", r"\bsports\b"
]

# =========================================================
# NEWS SOURCES
# =========================================================
NEWS_SOURCES = {
    "The Hindu": {
        "domain": "thehindu.com",
        "reliability": 5
    },
    "Indian Express": {
        "domain": "indianexpress.com",
        "reliability": 5
    },
    "Deccan Chronicle": {
        "domain": "deccanchronicle.com",
        "reliability": 4
    },
    "Times of India": {
        "domain": "timesofindia.indiatimes.com",
        "reliability": 4
    },
    "Business Standard": {
        "domain": "business-standard.com",
        "reliability": 4
    },
    "Hindu BusinessLine": {
        "domain": "thehindubusinessline.com",
        "reliability": 4
    }
}

# =========================================================
# ARTICLE PROCESSOR
# =========================================================
class ArticleProcessor:
    """Handles article extraction and cleaning"""
    
    @staticmethod
    def extract_text(html: str) -> Optional[str]:
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove unwanted tags
            for tag in soup(["script", "style", "footer", "nav", "aside", 
                           "header", "iframe", "noscript", "form"]):
                tag.decompose()
            
            # Try multiple extraction strategies
            text_parts = []
            
            # Strategy 1: Article tags
            article = soup.find("article")
            if article:
                text_parts.extend([p.get_text(strip=True) for p in article.find_all("p")])
            
            # Strategy 2: Main content area
            if not text_parts:
                main = soup.find("main") or soup.find(class_=re.compile(r"(article|content|story)"))
                if main:
                    text_parts.extend([p.get_text(strip=True) for p in main.find_all("p")])
            
            # Strategy 3: All paragraphs
            if not text_parts:
                text_parts = [p.get_text(strip=True) for p in soup.find_all("p")]
            
            # Filter out short paragraphs (likely navigation/ads)
            text_parts = [p for p in text_parts if len(p) > 50]
            
            text = " ".join(text_parts)
            text = re.sub(r"\s+", " ", text).strip()
            
            return text if len(text) >= CONFIG.min_article_length else None
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return None
    
    @staticmethod
    def extract_date(html: str, url: str) -> Optional[datetime]:
        """Extract publication date from article"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Common date meta tags
            date_selectors = [
                ("meta", {"property": "article:published_time"}),
                ("meta", {"name": "publishdate"}),
                ("meta", {"name": "date"}),
                ("time", {"class": re.compile(r"date|time|publish")}),
            ]
            
            for tag, attrs in date_selectors:
                element = soup.find(tag, attrs)
                if element:
                    date_str = element.get("content") or element.get("datetime") or element.get_text()
                    if date_str:
                        # Try parsing various formats
                        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d %B %Y", "%B %d, %Y"]:
                            try:
                                return datetime.strptime(date_str[:19], fmt)
                            except:
                                continue
            
            # Try URL date patterns
            url_date_match = re.search(r"(\d{4})/(\d{2})/(\d{2})", url)
            if url_date_match:
                y, m, d = url_date_match.groups()
                return datetime(int(y), int(m), int(d))
                
        except Exception as e:
            logger.debug(f"Date extraction failed: {e}")
        
        return None

# =========================================================
# CONTENT VALIDATOR
# =========================================================
class ContentValidator:
    """Validates article relevance"""
    
    @staticmethod
    def is_hyderabad_focused(text: str) -> bool:
        """Check if article is about Hyderabad"""
        text_lower = text.lower()
        
        # Must mention Hyderabad
        if "hyderabad" not in text_lower:
            return False
        
        # Count Hyderabad mentions
        hyd_count = text_lower.count("hyderabad")
        
        # Check if other cities are more prominent
        other_cities = ["mumbai", "delhi", "bengaluru", "bangalore", "chennai", "kolkata", "pune"]
        for city in other_cities:
            if text_lower.count(city) > hyd_count:
                return False
        
        return True
    
    @staticmethod
    def matches_keywords(text: str) -> bool:
        """Check if article contains relevant keywords"""
        text_lower = text.lower()
        
        # Count keyword group matches
        group_matches = 0
        for group, keywords in KEYWORD_GROUPS.items():
            if any(kw in text_lower for kw in keywords):
                group_matches += 1
        
        # Require at least 2 keyword groups
        return group_matches >= 2
    
    @staticmethod
    def check_exclusions(text: str) -> bool:
        """Check if article should be excluded"""
        text_lower = text.lower()
        
        for pattern in EXCLUDE_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    @staticmethod
    def detect_locations(text: str) -> List[str]:
        """Detect West Hyderabad locations in text"""
        text_lower = text.lower()
        detected = []
        
        for location, data in WEST_HYD_LOCATIONS.items():
            for alias in data["aliases"]:
                # Use word boundaries for better matching
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, text_lower):
                    detected.append((location, data["priority"]))
                    break
        
        # Sort by priority and return location names
        detected.sort(key=lambda x: x[1])
        return [loc for loc, _ in detected]
    
    @classmethod
    def validate(cls, text: str) -> Optional[Dict]:
        """Complete validation pipeline"""
        if not cls.is_hyderabad_focused(text):
            return None
        
        if cls.check_exclusions(text):
            return None
        
        if not cls.matches_keywords(text):
            return None
        
        locations = cls.detect_locations(text)
        if not locations:
            return None
        
        return {
            "primary_location": locations[0],
            "all_locations": locations
        }

# =========================================================
# NEWS FETCHER
# =========================================================
class NewsFetcher:
    """Handles web requests and article fetching"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
    
    def fetch_with_retry(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic"""
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(url, timeout=self.config.timeout)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Status {response.status_code} for {url}")
                    return None
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout attempt {attempt + 1} for {url}")
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None
        
        return None
    
    def search_google_news(self, query: str, date_range: Dict) -> List[str]:
        """Search Google News and extract article URLs"""
        search_query = f'{query} Hyderabad {date_range["month"]} {date_range["year"]}'
        
        # Try both site-specific and general searches
        urls = set()
        
        for source_name, source_data in NEWS_SOURCES.items():
            site_query = f'site:{source_data["domain"]} {search_query}'
            search_url = f"https://www.google.com/search?q={quote_plus(site_query)}&tbm=nws"
            
            response = self.fetch_with_retry(search_url)
            if response:
                extracted = self._extract_links_from_google(response.text, source_data["domain"])
                urls.update(extracted)
                time.sleep(self.config.request_delay)
        
        return list(urls)
    
    def _extract_links_from_google(self, html: str, domain: str) -> Set[str]:
        """Extract article URLs from Google search results"""
        soup = BeautifulSoup(html, "html.parser")
        urls = set()
        
        # Multiple strategies for link extraction
        for a in soup.find_all("a", href=True):
            href = a["href"]
            
            # Strategy 1: Direct URLs
            if domain in href and href.startswith("http"):
                urls.add(href.split("&")[0])
            
            # Strategy 2: Google redirect URLs
            elif "/url?q=" in href:
                try:
                    url = href.split("/url?q=")[1].split("&")[0]
                    if domain in url:
                        urls.add(url)
                except:
                    pass
        
        return urls
    
    def fetch_article(self, url: str) -> Optional[Dict]:
        """Fetch and process a single article"""
        response = self.fetch_with_retry(url)
        if not response:
            return None
        
        processor = ArticleProcessor()
        text = processor.extract_text(response.text)
        
        if not text:
            return None
        
        date = processor.extract_date(response.text, url)
        
        return {
            "url": url,
            "content": text,
            "date": date,
            "length": len(text)
        }

# =========================================================
# MAIN SCRAPER
# =========================================================
class WestHyderabadScraper:
    """Main scraper orchestrator"""
    
    def __init__(self, config: ScraperConfig = None):
        self.config = config or CONFIG
        self.db = BaseScraper()
        self.fetcher = NewsFetcher(self.config)
        self.validator = ContentValidator()
        self.stats = {
            "processed": 0,
            "inserted": 0,
            "duplicates": 0,
            "validation_failed": 0,
            "fetch_failed": 0
        }
    
    def generate_search_queries(self) -> List[str]:
        """Generate diverse search queries"""
        queries = []
        
        # Location + keyword combinations
        for location, data in WEST_HYD_LOCATIONS.items():
            primary_alias = data["aliases"][0]
            for group_name, keywords in KEYWORD_GROUPS.items():
                queries.append(f"{primary_alias} {keywords[0]}")
        
        # Broad infrastructure queries
        queries.extend([
            "west hyderabad metro",
            "outer ring road hyderabad",
            "gachibowli infrastructure",
            "financial district development",
            "hitec city expansion"
        ])
        
        return queries
    
    def scrape_month(self, target_date: datetime):
        """Scrape articles for a specific month"""
        date_range = {
            "month": target_date.strftime("%B"),
            "year": target_date.year
        }
        
        logger.info(f"📅 Scraping {date_range['month']} {date_range['year']}")
        
        queries = self.generate_search_queries()
        
        for query in queries:
            logger.debug(f"Query: {query}")
            
            # Search for articles
            urls = self.fetcher.search_google_news(query, date_range)
            logger.info(f"Found {len(urls)} URLs for '{query}'")
            
            for url in urls:
                self.process_article(url)
                time.sleep(self.config.article_delay)
        
        logger.info(f"Month summary: {self.stats}")
    
    def process_article(self, url: str):
        """Process a single article"""
        self.stats["processed"] += 1
        
        # Check for duplicates
        if self.db.is_duplicate(url):
            self.stats["duplicates"] += 1
            logger.debug(f"Duplicate: {url}")
            return
        
        # Fetch article
        article = self.fetcher.fetch_article(url)
        if not article:
            self.stats["fetch_failed"] += 1
            return
        
        # Validate content
        validation = self.validator.validate(article["content"])
        if not validation:
            self.stats["validation_failed"] += 1
            logger.debug(f"Validation failed: {url}")
            return
        
        # Get location ID
        location_id = self.db.get_location_id(validation["primary_location"])
        if not location_id:
            logger.error(f"Location ID not found: {validation['primary_location']}")
            return
        
        # Determine source
        source = self._identify_source(url)
        
        # Insert to database
        self.db.insert_raw_data(
            location_id=location_id,
            source=source,
            url=url,
            content=article["content"]
        )
        
        self.stats["inserted"] += 1
        logger.info(f"✔ Inserted: {validation['primary_location']} | {source}")
    
    def _identify_source(self, url: str) -> str:
        """Identify news source from URL"""
        domain = urlparse(url).netloc
        
        for source_name, source_data in NEWS_SOURCES.items():
            if source_data["domain"] in domain:
                return source_name
        
        return "Unknown Source"
    
    def run(self, months_back: int = 24):
        """Main execution method"""
        logger.info("🚀 West Hyderabad Long-Term News Scraper Started")
        logger.info(f"📆 Coverage: {months_back} months")
        
        today = datetime.today()
        
        for i in range(months_back):
            target = today - relativedelta(months=i)
            self.scrape_month(target)
        
        self.print_summary()
        self.db.close()
    
    def print_summary(self):
        """Print final statistics"""
        logger.info("\n" + "="*50)
        logger.info("🎯 FINAL SUMMARY")
        logger.info("="*50)
        
        for key, value in self.stats.items():
            logger.info(f"{key.replace('_', ' ').title():<20}: {value:>6}")
        
        if self.stats["processed"] > 0:
            success_rate = (self.stats["inserted"] / self.stats["processed"]) * 100
            logger.info(f"{'Success Rate':<20}: {success_rate:>5.1f}%")
        
        logger.info("="*50)
        logger.info("✅ Scraping completed")

# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    scraper = WestHyderabadScraper()
    scraper.run(months_back=24)