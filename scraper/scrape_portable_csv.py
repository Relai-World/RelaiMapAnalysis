
import asyncio
from playwright.async_api import async_playwright
import feedparser
import csv
import os
import time
import random
import logging
import argparse
from datetime import datetime
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIG (Mirror of Main Scraper) ---
TARGET_PER_THEME_PER_YEAR = 10 
THEMES = {
    "Real Estate": "real estate OR property prices OR apartments OR new launches",
    "Infrastructure": "infrastructure OR metro OR flyover OR road widening OR water supply",
    "Safety": "crime OR police OR accident OR theft OR safety",
    "Lifestyle": "mall OR park OR hospital OR school OR restaurant",
    "Corporate": "office opening OR tech park OR jobs OR hiring"
}

ALIASES = {
    "Kajaguda": ["Khajaguda"], "Khajaguda": ["Kajaguda"], "BEERAMGUDA": ["Beeramguda"],
    "Tellapur": ["Telapur"], "Kollur": ["Kolur"], "Narsingi": ["Narasingi"],
    "Financial District": ["Nanakramguda", "ISB Road"], "Hitech City": ["HITEC City"]
}

class PortableScraper:
    def __init__(self, output_file="scraped_results.csv"):
        self.output_file = output_file
        self.init_csv()

    def init_csv(self):
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["location_name", "category", "source", "url", "content", "published_at", "scraped_at"])

    def generate_variants(self, name):
        variants = {f'"{name}"'}
        if name in ALIASES:
            for a in ALIASES[name]: variants.add(f'"{a}"')
        name_lower = name.lower()
        if 'th' in name_lower: variants.add(f'"{name_lower.replace("th", "t").title()}"')
        if 'dh' in name_lower: variants.add(f'"{name_lower.replace("dh", "d").title()}"')
        if name_lower == "kajaguda": variants.add('"Khajaguda"')
        return list(variants)

    async def run(self, locations_list):
        print(f"🚀 STARTING PORTABLE SCRAPER | Output: {self.output_file}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            page = await context.new_page()

            for idx, location in enumerate(locations_list):
                print(f"\n📍 [{idx+1}/{len(locations_list)}] Processing: {location}")
                variants = self.generate_variants(location)
                location_query = f"({' OR '.join(variants)})"
                
                BUCKETS = [("Historical", "2021-01-01", "2023-12-31"), ("Recent", "2024-01-01", "2026-12-31")]

                for theme_name, theme_query in THEMES.items():
                    for bucket_label, start_date, end_date in BUCKETS:
                        full_query = f'{location_query} Hyderabad ({theme_query}) after:{start_date} before:{end_date}'
                        rss_url = f"https://news.google.com/rss/search?q={quote_plus(full_query)}&hl=en-IN&gl=IN&ceid=IN:en"
                        
                        feed = feedparser.parse(rss_url)
                        if not feed.entries: continue
                        
                        success_count = 0
                        for entry in feed.entries:
                            if success_count >= (TARGET_PER_THEME_PER_YEAR * 3): break
                            
                            try:
                                await page.goto(entry.link, wait_until="load", timeout=15000)
                                if "google.com" in page.url: await page.wait_for_url(lambda u: "google.com" not in u, timeout=8000)
                                
                                final_url = page.url
                                content = await page.content()
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(content, 'html.parser')
                                for s in soup(['script', 'style', 'nav', 'footer']): s.decompose()
                                text = ' '.join(soup.get_text().split())[:5000]
                                
                                if len(text) < 300: continue

                                source = entry.source.title if hasattr(entry, 'source') else 'News'
                                pub_date = entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d")

                                with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerow([location, theme_name, source, final_url, text, pub_date, datetime.now().isoformat()])
                                
                                success_count += 1
                                print(f"      ✅ Saved: {entry.title[:50]}...")
                                time.sleep(random.uniform(1, 2))
                            except: pass

                        time.sleep(random.uniform(4, 7))

            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--locations", type=str, required=True, help="Comma separated locations")
    args = parser.parse_args()
    
    locs = [l.strip() for l in args.locations.split(",")]
    scraper = PortableScraper()
    asyncio.run(scraper.run(locs))
