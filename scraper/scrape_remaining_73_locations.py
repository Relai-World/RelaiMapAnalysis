#!/usr/bin/env python3

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

class CompleteFutureDevelopmentScraper:
    def __init__(self):
        # Initialize Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        
        self.supabase: Client = create_client(url, key)
        logger.info("📁 Connected to Supabase")

    def extract_year_from_content(self, content):
        """Extract year mentions from 2023-2030 range"""
        years = []
        # Look for years 2023-2030
        for year in range(2023, 2031):
            if str(year) in content:
                years.append(year)
        
        # Also look for phrases like "expected by 2025", "completion in 2026", etc.
        completion_patterns = [
            r'expected (?:by|in) (\d{4})',
            r'completion (?:by|in) (\d{4})',
            r'ready by (\d{4})',
            r'launch(?:ed)? in (\d{4})',
            r'opening in (\d{4})',
            r'scheduled for (\d{4})'
        ]
        
        for pattern in completion_patterns:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                year = int(match)
                if 2023 <= year <= 2030 and year not in years:
                    years.append(year)
        
        return max(years) if years else None

    def insert_article(self, loc_id, location, source, url, content, pub_at, year_mentioned):
        try:
            # Check if URL already exists
            result = self.supabase.table('future_development_scrap').select('id').eq('url', url).execute()
            if result.data and len(result.data) > 0:
                return False, "duplicate_db"

            # Insert new article
            data = {
                'location_id': loc_id,
                'location_name': location,
                'source': source,
                'url': url,
                'content': content,
                'published_at': pub_at if pub_at else datetime.now().isoformat(),
                'year_mentioned': year_mentioned,
                'scraped_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('future_development_scrap').insert(data).execute()
            return True, "success"
        except Exception as e:
            logger.error(f"DB Insert Error: {e}")
            return False, f"error: {e}"

    def get_location_count(self, loc_id):
        try:
            result = self.supabase.table('future_development_scrap').select('id', count='exact').eq('location_id', loc_id).execute()
            return result.count if result.count else 0
        except:
            return 0

    def get_remaining_locations(self):
        """Get all 73 remaining locations that need to be scraped"""
        try:
            # Get all Hyderabad locations
            result = self.supabase.rpc('get_all_insights').execute()
            if not result.data:
                return []
                
            # Filter Hyderabad locations (17°N, 78°E)
            hyderabad_locations = []
            for loc in result.data:
                lat = loc.get('latitude')
                lng = loc.get('longitude')
                if lat and lng and (17.0 <= lat <= 18.0) and (78.0 <= lng <= 79.0):
                    hyderabad_locations.append((loc['location_id'], loc['location']))
            
            # Get already scraped locations
            scraped_response = self.supabase.table('future_development_scrap').select('location_name').execute()
            scraped_locations = set([loc['location_name'] for loc in scraped_response.data])
            
            # Find missing locations
            missing_locations = []
            for loc_id, location in hyderabad_locations:
                if location not in scraped_locations:
                    missing_locations.append((loc_id, location))
            
            # Sort by location name for consistent processing
            missing_locations.sort(key=lambda x: x[1].lower())
            
            print(f"🎯 FOUND {len(missing_locations)} REMAINING LOCATIONS TO SCRAPE:")
            print(f"=" * 70)
            
            # Group by priority (high-property locations first)
            # Get property counts for prioritization
            properties_response = self.supabase.table('unified_data_DataType_Raghu').select('areaname').execute()
            from collections import Counter
            location_counts = Counter([prop['areaname'] for prop in properties_response.data if prop.get('areaname')])
            
            # Add property counts and sort by priority
            missing_with_counts = []
            for loc_id, location in missing_locations:
                count = location_counts.get(location, 0)
                missing_with_counts.append((loc_id, location, count))
            
            # Sort by property count (high priority first)
            missing_with_counts.sort(key=lambda x: x[2], reverse=True)
            
            print(f"📊 TOP 20 HIGH-PRIORITY LOCATIONS:")
            for i, (loc_id, location, count) in enumerate(missing_with_counts[:20], 1):
                print(f"{i:2d}. {location}: {count} properties (ID: {loc_id})")
            
            if len(missing_with_counts) > 20:
                print(f"... and {len(missing_with_counts) - 20} more locations")
            
            # Return just the location tuples (without counts)
            return [(loc_id, location) for loc_id, location, count in missing_with_counts]
            
        except Exception as e:
            logger.error(f"❌ Error getting remaining locations: {e}")
            return []

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
                    print(f"         Saved ({added}/{target_count}){year_tag}: {entry.title[:50]}...")
                else:
                    skipped += 1
                
                time.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                skipped += 1
                continue
        
        return added, skipped

    async def run(self, locations_data):
        print("🚀 SCRAPING ALL 73 REMAINING LOCATIONS FOR FUTURE DEVELOPMENT")
        print(f"Target: Articles about future developments (2023-2030)")
        print(f"Goal: {ARTICLES_PER_LOCATION} articles per location")
        print(f"Locations to process: {len(locations_data)}\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()

            total_processed = 0
            total_articles_added = 0

            for idx, (loc_id, location) in enumerate(locations_data):
                print(f"\n{'='*70}")
                print(f"[{idx+1}/{len(locations_data)}] Processing: {location} (ID: {loc_id})")
                print(f"{'='*70}")
                
                current_count = self.get_location_count(loc_id)
                print(f"   Current records in DB: {current_count}")
                
                if current_count >= ARTICLES_PER_LOCATION:
                    print(f"   Already has {current_count} articles, skipping...")
                    continue
                
                processed_urls = set()
                location_total = 0
                remaining = ARTICLES_PER_LOCATION - current_count
                
                # Try different query variations
                for query_idx, dev_query in enumerate(FUTURE_DEV_QUERIES, 1):
                    if location_total >= remaining:
                        break
                    
                    print(f"\n   Query {query_idx}/{len(FUTURE_DEV_QUERIES)}")
                    
                    # Add date range to query (2023 onwards)
                    full_query = f'{location} Hyderabad ({dev_query}) 2023..2030'
                    entries = await self.fetch_google_news(full_query)
                    
                    if not entries:
                        print(f"      No articles found")
                        continue
                    
                    print(f"      Found {len(entries)} articles")
                    
                    target_for_query = min(5, remaining - location_total)  # Max 5 per query
                    added, skipped = await self.process_articles(
                        page, entries, loc_id, location, processed_urls, target_for_query
                    )
                    location_total += added
                    
                    print(f"      Added: {added}, Skipped: {skipped}")

                    time.sleep(random.uniform(2, 4))
                
                final_count = self.get_location_count(loc_id)
                print(f"\n   Location Summary: {location_total} new articles")
                print(f"   Total in DB: {final_count}")
                print(f"   Target: {ARTICLES_PER_LOCATION}, Progress: {final_count}/{ARTICLES_PER_LOCATION}")
                
                total_processed += 1
                total_articles_added += location_total

            await browser.close()
        
        print(f"\n{'='*70}")
        print(f"🎉 SCRAPING COMPLETE!")
        print(f"{'='*70}")
        print(f"Locations processed: {total_processed}")
        print(f"Total articles added: {total_articles_added}")
        print(f"Average articles per location: {total_articles_added/total_processed:.1f}" if total_processed > 0 else "")

if __name__ == "__main__":
    scraper = CompleteFutureDevelopmentScraper()
    try:
        # Get all remaining locations
        locations = scraper.get_remaining_locations()
        
        if not locations:
            logger.error("❌ No remaining locations found. Exiting...")
        else:
            logger.info(f"🎯 Starting scraper for {len(locations)} remaining locations")
            asyncio.run(scraper.run(locations))
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Scraper error: {e}")