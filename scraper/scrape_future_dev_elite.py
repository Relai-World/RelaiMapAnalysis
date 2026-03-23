"""
Elite Future Development Scraper for Hyderabad Locations
Precision-focused scraper that extracts ONLY relevant future development articles
for each specific location (2022-2030+)

Author: Claude Sonnet 4.5
"""

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
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('future_dev_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
ARTICLES_PER_LOCATION = 15  # Realistic target - quality over quantity
MIN_CONTENT_LENGTH = 500  # Slightly lower minimum
MAX_CONTENT_LENGTH = 8000  # Maximum content to store

# All 169 Hyderabad Locations with IDs
HYDERABAD_LOCATIONS = [
    (35, "Abids"), (36, "Adibatla"), (37, "Alkapur"), (38, "Alwal"),
    (256, "Amberpet"), (39, "Ameenpur"), (40, "Annojiguda"), (41, "Appa Junction"),
    (43, "Ashok Nagar"), (44, "Attapur"), (47, "Bacharam"), (48, "Bachupally"),
    (50, "Bahadurpally"), (53, "Bandlaguda"), (52, "Bandlaguda Jagir"), (54, "Banjara Hills"),
    (46, "Beeramguda"), (56, "Begumpet"), (61, "Boduppal"), (62, "Bolarum"),
    (63, "Bollaram"), (64, "Bowrampet"), (66, "Budvel"), (67, "Chandanagar"),
    (68, "Chegur"), (69, "Chengicherla"), (70, "Chevella"), (72, "Chiryala"),
    (73, "Chitkul"), (75, "Damaragidda"), (76, "Dammaiguda"), (260, "Depalle"),
    (257, "Dollar Hills"), (80, "Dulapally"), (81, "Dundigal"), (5, "Financial District"),
    (1, "Gachibowli"), (251, "Gagillapur"), (83, "Gajularamaram"), (84, "Gandamguda"),
    (85, "Gandi Maisamma"), (86, "Gandipet"), (87, "Ghatkesar"), (88, "Gollur"),
    (89, "Gopanpally"), (90, "Gowdavalli"), (243, "Gowrelly"), (91, "Gundlapochampally"),
    (95, "Habsiguda"), (96, "Hafeezpet"), (97, "Hakimpet"), (98, "Hastinapuram"),
    (99, "Hayathnagar"), (102, "Himayat Nagar"), (3, "Hitec City"), (107, "Ibrahimpatnam"),
    (109, "Injapur"), (110, "Isnapur"), (113, "Jeedimetla"), (114, "Jubilee Hills"),
    (116, "Kachiguda"), (118, "Kalyan Nagar"), (119, "Kamalanagar"), (121, "Kandawada"),
    (122, "Kandlakoya"), (123, "Kandukur"), (124, "Kapra"), (125, "Karmanghat"),
    (126, "Kavadiguda"), (127, "Keesara"), (117, "Khajaguda"), (129, "Kismatpur"),
    (132, "Kokapet"), (133, "Kollur"), (134, "Kompally"), (255, "Konapur"),
    (2, "Kondapur"), (135, "Kongara Kalan"), (137, "Kothaguda"), (138, "Kothapet"),
    (139, "Kothur"), (140, "Kowkoor"), (141, "Krishnareddypet"), (7, "Kukatpally"),
    (142, "LB Nagar"), (144, "Lakdikapul"), (145, "Laxmiguda"), (252, "Lingampally"),
    (147, "Madeenaguda"), (4, "Madhapur"), (148, "Maheshwaram"), (149, "Malkajgiri"),
    (150, "Mallampet"), (151, "Mallapur"), (152, "Mamidipally"), (153, "Manchirevula"),
    (154, "Mangalpalli"), (155, "Manikonda"), (156, "Manneguda"), (157, "Mansanpally"),
    (158, "Mansoorabad"), (159, "Medchal"), (160, "Medipally"), (161, "Meerpet"),
    (162, "Mehdipatnam"), (163, "Miyapur"), (146, "Mokila"), (165, "Moosapet"),
    (166, "Moti Nagar"), (167, "Moula Ali"), (168, "Muthangi"), (170, "Nacharam"),
    (171, "Nadergul"), (172, "Nagaram"), (173, "Nagole"), (174, "Nallagandla"),
    (176, "Nallakunta"), (6, "Nanakramguda"), (177, "Narapally"), (178, "Narsingi"),
    (179, "Neknampur"), (180, "Neopolis"), (181, "Nizampet"), (184, "Osman Nagar"),
    (187, "Palgutta"), (188, "Patancheru"), (191, "Patighanpur"), (192, "Peeramcheruvu"),
    (194, "Peerzadiguda"), (195, "Pocharam"), (196, "Podur"), (197, "Pragathi Nagar"),
    (258, "Punjagutta"), (198, "Puppalaguda"), (200, "Quthbullapur"), (202, "Rajendra Nagar"),
    (254, "Ramachandrapuram"), (203, "Rampally"), (250, "Raviryal"), (204, "Rudraram"),
    (206, "Saidabad"), (207, "Sainikpuri"), (208, "Sanath Nagar"), (186, "Secunderabad"),
    (213, "Serilingampally"), (215, "Shadnagar"), (216, "Shaikpet"), (217, "Shamirpet"),
    (218, "Shamshabad"), (219, "Shamsherganj"), (220, "Shankarpally"), (253, "Shilpa Hills"),
    (259, "Sirigiripuram"), (221, "Somajiguda"), (222, "Suchitra"), (223, "Suraram"),
    (225, "Tarnaka"), (224, "Tellapur"), (228, "Thumkunta"), (229, "Tooroor"),
    (230, "Tukkuguda"), (231, "Turkapally"), (232, "Turkayamjal"), (233, "Uppal"),
    (234, "Uppal Bhagath"), (236, "Velimela"), (238, "Yamnampet"), (239, "Yapral"),
    (242, "Yousufguda")
]

# Highly specific future development queries
FUTURE_DEV_QUERIES = [
    # Primary queries - most specific
    '"upcoming project" OR "new project" OR "infrastructure project"',
    '"metro line" OR "metro station" OR "metro corridor"',
    '"residential project" OR "apartment launch" OR "gated community"',
    '"IT park" OR "tech park" OR "SEZ" OR "business park"',
    '"mall" OR "shopping complex" OR "commercial complex"',
    '"flyover" OR "road widening" OR "elevated corridor"',
    
    # Secondary queries - broader but still relevant
    'development OR infrastructure OR construction after:2022',
    '"real estate" OR "property launch" OR builder',
    '"GHMC project" OR "HMDA project" OR "smart city"',
    'connectivity OR transport OR airport',
    
    # Fallback queries - very broad
    'future OR upcoming OR planned after:2022',
    'new OR opening OR launch after:2022'
]


class EliteFutureDevelopmentScraper:
    def __init__(self):
        # Initialize Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        
        self.supabase: Client = create_client(url, key)
        self._verify_table()
        logger.info("📁 Connected to Supabase - future_dev table ready")

    def _verify_table(self):
        """Verify table exists"""
        try:
            result = self.supabase.table('future_dev').select('id').limit(1).execute()
            logger.info("Table future_dev verified successfully")
        except Exception as e:
            logger.error(f"Table verification failed: {e}")
            logger.info("Please run create_future_dev_table.sql in Supabase SQL Editor")
            print("\n" + "="*80)
            print("ERROR: Table 'future_dev' does not exist in Supabase!")
            print("="*80)
            print("\nPlease follow these steps:")
            print("1. Go to your Supabase Dashboard")
            print("2. Open SQL Editor")
            print("3. Copy and paste the contents of 'create_future_dev_table.sql'")
            print("4. Run the SQL script")
            print("5. Run this scraper again")
            print("="*80 + "\n")
            raise

    def extract_years_from_content(self, content):
        """Extract year mentions from 2022-2030 range with intelligent parsing"""
        years = set()
        
        # Direct year mentions (2022-2030)
        for year in range(2022, 2031):
            if str(year) in content:
                years.add(year)
        
        # Contextual year extraction patterns
        completion_patterns = [
            r'(?:expected|scheduled|planned|targeted|slated|due)(?:\s+to\s+be)?(?:\s+completed?)?(?:\s+by|\s+in|\s+for)\s+(\d{4})',
            r'completion\s+(?:by|in|date)\s+(\d{4})',
            r'ready\s+by\s+(\d{4})',
            r'launch(?:ed|ing)?\s+in\s+(\d{4})',
            r'opening\s+in\s+(\d{4})',
            r'(?:will|to)\s+be\s+(?:completed|ready|operational)\s+(?:by|in)\s+(\d{4})',
            r'by\s+(?:end\s+of\s+)?(\d{4})',
            r'in\s+the\s+year\s+(\d{4})'
        ]
        
        for pattern in completion_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                year = int(match)
                if 2022 <= year <= 2030:
                    years.add(year)
        
        # Return the latest year (most likely completion/target year)
        return max(years) if years else None

    def is_future_development_article(self, content, title=""):
        """
        Check if article is ACTUALLY about future development/infrastructure projects
        Balanced approach - not too strict, not too lenient
        """
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        combined = content_lower + " " + title_lower
        
        # Strong future development indicators (need at least 1)
        strong_indicators = [
            'upcoming project', 'future development', 'planned project',
            'proposed project', 'new project', 'infrastructure project',
            'construction project', 'development plan', 'master plan',
            'will be built', 'will be developed', 'will be constructed',
            'to be built', 'to be developed', 'to be constructed',
            'under construction', 'construction of', 'development of',
            'metro line', 'metro station', 'metro corridor', 'metro rail',
            'flyover', 'elevated corridor', 'road widening', 'expressway',
            'new mall', 'shopping complex', 'commercial complex',
            'it park', 'tech park', 'business park', 'sez', 'special economic zone',
            'residential project', 'apartment project', 'housing project',
            'gated community', 'township', 'villa project',
            'approved project', 'sanctioned project', 'tender for',
            'real estate launch', 'property launch', 'builder launch',
            'infrastructure development', 'urban development',
            'connectivity project', 'transport project'
        ]
        
        # Medium indicators (need at least 2 if no strong indicator)
        medium_indicators = [
            'upcoming', 'future', 'planned', 'proposed', 'new development',
            'construction', 'launch', 'opening', 'expansion',
            'infrastructure', 'development', 'project announced',
            'ghmc', 'hmda', 'development authority'
        ]
        
        # Count indicators
        strong_count = sum(1 for ind in strong_indicators if ind in combined)
        medium_count = sum(1 for ind in medium_indicators if ind in combined)
        
        # Accept if has strong indicator OR multiple medium indicators
        has_development_content = strong_count >= 1 or medium_count >= 3
        
        if not has_development_content:
            return False
        
        # MUST NOT be primarily about these topics (hard reject)
        hard_reject_indicators = [
            'crime', 'theft', 'robbery', 'murder', 'assault', 'arrested',
            'accident', 'death', 'died', 'killed', 'injured', 'fatal',
            'vape', 'cigarette', 'drug', 'gang', 'smuggling',
            'movie', 'film', 'actor', 'actress', 'cinema release',
            'cricket match', 'tournament', 'sports event',
            'festival celebration', 'concert', 'music event'
        ]
        
        # Count hard rejects
        hard_reject_count = sum(1 for neg in hard_reject_indicators if neg in combined)
        
        # If more than 1 hard reject indicator, reject
        if hard_reject_count > 1:
            return False
        
        # Soft reject indicators (reject if too many)
        soft_reject_indicators = [
            'protest', 'strike', 'election', 'voting',
            'weather', 'rain', 'flood warning',
            'covid', 'pandemic', 'lockdown',
            'traffic jam', 'traffic congestion',
            'historic', 'heritage', 'ancient'
        ]
        
        soft_reject_count = sum(1 for neg in soft_reject_indicators if neg in combined)
        
        # If more than 3 soft rejects, reject
        if soft_reject_count > 3:
            return False
        
        return True

    def is_location_relevant(self, content, location_name):
        """
        Balanced relevance check - ensures article is about this specific location
        Not too strict to miss good articles, not too lenient to accept bad ones
        """
        content_lower = content.lower()
        location_lower = location_name.lower()
        
        # Must contain location name
        if location_lower not in content_lower:
            return False
        
        # Count occurrences
        occurrence_count = content_lower.count(location_lower)
        
        # For very specific locations, 1 mention might be enough if in good context
        # For common locations, need at least 2
        min_occurrences = 1 if len(location_lower) > 8 else 2
        
        if occurrence_count < min_occurrences:
            return False
        
        # Check if article is primarily about OTHER major locations
        major_other_locations = [
            "gachibowli", "kondapur", "hitec city", "madhapur", "financial district",
            "nanakramguda", "kukatpally", "miyapur", "bachupally",
            "secunderabad", "banjara hills", "jubilee hills", "begumpet",
            "lb nagar", "uppal", "mehdipatnam", "manikonda", "kokapet"
        ]
        
        # Remove current location
        major_other_locations = [loc for loc in major_other_locations if loc != location_lower]
        
        # Count major location mentions
        other_major_count = sum(content_lower.count(loc) for loc in major_other_locations)
        
        # If other major locations mentioned MORE than 2x target location, likely wrong article
        if other_major_count > (occurrence_count * 2):
            return False
        
        # Check for development keywords near location mentions
        development_keywords = [
            'upcoming', 'future', 'planned', 'proposed', 'new', 'development',
            'project', 'construction', 'launch', 'opening', 'expansion',
            'infrastructure', 'metro', 'road', 'flyover', 'mall', 'apartment',
            'residential', 'commercial', 'it park', 'builder', 'real estate'
        ]
        
        # Find location mentions and check context
        location_positions = [m.start() for m in re.finditer(re.escape(location_lower), content_lower)]
        
        has_relevant_context = False
        for pos in location_positions:
            # Check 300 characters around location mention
            context_start = max(0, pos - 300)
            context_end = min(len(content_lower), pos + len(location_lower) + 300)
            context = content_lower[context_start:context_end]
            
            # If any development keyword in context, it's relevant
            if any(keyword in context for keyword in development_keywords):
                has_relevant_context = True
                break
        
        return has_relevant_context

    def insert_article(self, loc_id, location, source, url, content, pub_at, year_mentioned):
        """Insert article into Supabase"""
        try:
            # Check if URL already exists
            result = self.supabase.table('future_dev').select('id').eq('url', url).execute()
            if result.data and len(result.data) > 0:
                return False, "duplicate"

            # Prepare data
            data = {
                'location_id': loc_id,
                'location_name': location,
                'source': source,
                'url': url,
                'content': content[:MAX_CONTENT_LENGTH],  # Limit content size
                'published_at': pub_at if pub_at else datetime.now().isoformat(),
                'year_mentioned': year_mentioned,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Insert
            result = self.supabase.table('future_dev').insert(data).execute()
            return True, "success"
        except Exception as e:
            logger.error(f"DB Insert Error for {location}: {e}")
            return False, f"error: {str(e)[:100]}"

    def get_location_count(self, loc_id):
        """Get current article count for location"""
        try:
            result = self.supabase.table('future_dev').select('id', count='exact').eq('location_id', loc_id).execute()
            return result.count if result.count else 0
        except:
            return 0

    async def fetch_google_news(self, query):
        """Fetch Google News RSS feed"""
        rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            resp = requests.get(
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=15
            )
            feed = feedparser.parse(resp.content)
            return feed.entries if feed and feed.entries else []
        except Exception as e:
            logger.warning(f"RSS fetch error: {e}")
            return []

    async def process_articles(self, page, feed_entries, loc_id, location, processed_urls, target_count):
        """Process articles with strict relevance filtering"""
        added = 0
        skipped_duplicate = 0
        skipped_irrelevant = 0
        skipped_short = 0
        skipped_no_year = 0
        
        for entry in feed_entries:
            if added >= target_count:
                break
            
            entry_url = getattr(entry, 'link', None)
            if not entry_url or entry_url in processed_urls:
                skipped_duplicate += 1
                continue
            
            try:
                # Navigate to article
                await page.goto(entry.link, wait_until="load", timeout=15000)
                
                # Handle Google News redirect
                if "google.com" in page.url:
                    await page.wait_for_url(lambda u: "google.com" not in u, timeout=8000)
                
                final_url = page.url
                
                if final_url in processed_urls:
                    skipped_duplicate += 1
                    continue
                
                # Extract content
                content_html = await page.content()
                soup = BeautifulSoup(content_html, 'html.parser')
                
                # Remove noise
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                    tag.decompose()
                
                text = ' '.join(soup.get_text().split())
                
                # Length check
                if len(text) < MIN_CONTENT_LENGTH:
                    skipped_short += 1
                    continue

                # CRITICAL 1: Must be about future development (not general news)
                title = entry.title if hasattr(entry, 'title') else ''
                if not self.is_future_development_article(text, title):
                    skipped_irrelevant += 1
                    logger.debug(f"Rejected (not future dev): {title[:80]}")
                    continue

                # CRITICAL 2: Strict location relevance check
                if not self.is_location_relevant(text, location):
                    skipped_irrelevant += 1
                    logger.debug(f"Rejected (wrong location): {title[:80]}")
                    continue

                # Extract year
                year_mentioned = self.extract_years_from_content(text)
                
                # Must have a year mention for future development
                if not year_mentioned:
                    skipped_no_year += 1
                    continue
                
                # Extract metadata
                source = entry.source.title if hasattr(entry, 'source') else 'News'
                pub_at = entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Insert into database
                success, reason = self.insert_article(loc_id, location, source, final_url, text, pub_at, year_mentioned)
                
                if success:
                    added += 1
                    processed_urls.add(final_url)
                    title_preview = entry.title[:60] if hasattr(entry, 'title') else 'Article'
                    print(f"         ✅ [{added}/{target_count}] Year: {year_mentioned} | {title_preview}...")
                else:
                    if reason == "duplicate":
                        skipped_duplicate += 1
                
                # Respectful delay
                await asyncio.sleep(random.uniform(0.8, 1.8))
                
            except Exception as e:
                logger.debug(f"Article processing error: {str(e)[:100]}")
                skipped_irrelevant += 1
                continue
        
        return {
            'added': added,
            'skipped_duplicate': skipped_duplicate,
            'skipped_irrelevant': skipped_irrelevant,
            'skipped_short': skipped_short,
            'skipped_no_year': skipped_no_year
        }

    async def run(self, start_from_id=None):
        """Main scraper execution"""
        print("=" * 80)
        print("🚀 ELITE FUTURE DEVELOPMENT SCRAPER")
        print("=" * 80)
        print(f"📍 Locations: {len(HYDERABAD_LOCATIONS)}")
        print(f"🎯 Target: {ARTICLES_PER_LOCATION} articles per location")
        print(f"📅 Years: 2022-2030+")
        print(f"🔍 Precision Mode: STRICT location relevance filtering")
        print("=" * 80)
        
        # Filter locations if starting from specific ID
        locations_to_process = HYDERABAD_LOCATIONS
        if start_from_id:
            locations_to_process = [(lid, lname) for lid, lname in HYDERABAD_LOCATIONS if lid >= start_from_id]
            print(f"▶️  Starting from Location ID: {start_from_id}")
            print(f"📊 Processing {len(locations_to_process)} locations")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            for idx, (loc_id, location) in enumerate(locations_to_process, 1):
                print(f"\n{'='*80}")
                print(f"📍 [{idx}/{len(locations_to_process)}] {location} (ID: {loc_id})")
                print(f"{'='*80}")
                
                current_count = self.get_location_count(loc_id)
                print(f"   📊 Current DB count: {current_count}")
                
                if current_count >= ARTICLES_PER_LOCATION:
                    print(f"   ✅ Target reached ({current_count}/{ARTICLES_PER_LOCATION}), skipping...")
                    continue
                
                processed_urls = set()
                location_total = 0
                remaining = ARTICLES_PER_LOCATION - current_count
                
                # Try different query variations
                for query_idx, dev_query in enumerate(FUTURE_DEV_QUERIES, 1):
                    if location_total >= remaining:
                        print(f"   🎯 Target reached! ({location_total} new articles)")
                        break
                    
                    print(f"\n   🔍 Query {query_idx}/{len(FUTURE_DEV_QUERIES)}")
                    
                    # Construct query with location name in quotes for precision
                    full_query = f'"{location}" Hyderabad {dev_query}'
                    entries = await self.fetch_google_news(full_query)
                    
                    if not entries:
                        print(f"      ⚠️  No articles found")
                        continue
                    
                    print(f"      📰 Found {len(entries)} articles, processing...")
                    
                    # Process articles
                    target_for_query = min(3, remaining - location_total)  # Max 3 per query
                    stats = await self.process_articles(
                        page, entries, loc_id, location, processed_urls, target_for_query
                    )
                    
                    location_total += stats['added']
                    
                    print(f"      📊 Added: {stats['added']} | Skipped: Dup={stats['skipped_duplicate']}, "
                          f"Irrelevant={stats['skipped_irrelevant']}, Short={stats['skipped_short']}, "
                          f"NoYear={stats['skipped_no_year']}")

                    # Delay between queries
                    await asyncio.sleep(random.uniform(2.5, 4.5))
                
                final_count = self.get_location_count(loc_id)
                print(f"\n   ✅ Location Complete:")
                print(f"      • New articles: {location_total}")
                print(f"      • Total in DB: {final_count}/{ARTICLES_PER_LOCATION}")
                
                # Delay between locations
                await asyncio.sleep(random.uniform(3, 5))

            await browser.close()
        
        print(f"\n{'='*80}")
        print(f"🎉 SCRAPING COMPLETE!")
        print(f"{'='*80}")
        logger.info("Scraper session completed successfully")


if __name__ == "__main__":
    scraper = EliteFutureDevelopmentScraper()
    
    try:
        # Optional: Start from specific location ID
        # asyncio.run(scraper.run(start_from_id=35))
        
        # Run for all locations
        asyncio.run(scraper.run())
        
    except KeyboardInterrupt:
        logger.info("⚠️  Scraper interrupted by user")
    except Exception as e:
        logger.error(f"❌ Scraper error: {e}", exc_info=True)
