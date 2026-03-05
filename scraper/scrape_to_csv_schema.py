
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
import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIG (Matched to news_balanced_corpus schema) ---
TARGET_PER_THEME_PER_YEAR = 10 
THEMES = {
    "Real Estate": "real estate OR property prices OR apartments OR new launches",
    "Infrastructure": "infrastructure OR metro OR flyover OR road widening OR water supply",
    "Safety": "crime OR police OR accident OR theft OR safety",
    "Lifestyle": "mall OR park OR hospital OR school OR restaurant",
    "Corporate": "office opening OR tech park OR jobs OR hiring"
}

ALIASES = {
    "Kajaguda": ["Khajaguda"], 
    "Khajaguda": ["Kajaguda"], 
    "BEERAMGUDA": ["Beeramguda", "Bheeramguda"],
    "Tellapur": ["Telapur"], 
    "Kollur": ["Kolur"], 
    "Narsingi": ["Narasingi"],
    "Financial District": ["Nanakramguda", "ISB Road"], 
    "Hitech City": ["HITEC City", "HITEX"],
    "LB Nagar": ["Lal Bahadur Nagar", "L.B. Nagar"],
    "Manikonda": ["Manykonda"],
    "Miyapur": ["Myapur"],
    "Kokapet": ["Kokapeta"],
    "Mokila": ["Mokila Village"],
    "Karmanghat": ["Karmaanghat"],
    "Lakdikapool": ["Lakdi ka pul", "Lakdikapul"],
    "Keesara": ["Kesara"],
    "Kompally": ["Kompalli"],
    "Medipally": ["Medipalli"],
    "Moula Ali": ["Mouala Ali"],
    "Malkajgiri": ["Malkajigiri"],
    "Mehdipatnam": ["Mehadipatnam"],
    "Kothapet": ["Kothapeta"]
}

class PortableScraperCSV:
    def __init__(self, output_file="hyderabad_scraped_data.csv"):
        self.output_file = output_file
        self.init_csv()

    def init_csv(self):
        """Initialize CSV with headers matching news_balanced_corpus columns"""
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Matches DB exactly: location_id, location_name, source, url, content, published_at, category, scraped_at
                writer.writerow(["location_id", "location_name", "source", "url", "content", "published_at", "category", "scraped_at"])
            print(f"📁 Created CSV: {self.output_file}")

    def generate_variants(self, name):
        """Generates common variations of Indian location names"""
        variants = {f'"{name}"'}
        if name in ALIASES:
            for a in ALIASES[name]:
                variants.add(f'"{a}"')
        
        name_lower = name.lower()
        if 'th' in name_lower:
            variants.add(f'"{name_lower.replace("th", "t").title()}"')
        if 'dh' in name_lower:
            variants.add(f'"{name_lower.replace("dh", "d").title()}"')
        if 'kh' in name_lower:
            variants.add(f'"{name_lower.replace("kh", "k").title()}"')
            
        if name_lower == "kajaguda":
            variants.add('"Khajaguda"')
        elif name_lower == "khajaguda":
            variants.add('"Kajaguda"')

        if name.endswith('i'):
            variants.add(f'"{name[:-1]}y"')
        elif name.endswith('y'):
            variants.add(f'"{name[:-1]}i"')
            
        return list(variants)

    async def run(self, locations_data):
        """
        locations_data: list of tuples (id, name)
        """
        print(f"🚀 STARTING PORTABLE SCHEMA-MATCHED SCRAPER")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            for idx, (loc_id, location) in enumerate(locations_data):
                print(f"\n📍 [{idx+1}/{len(locations_data)}] Processing: {location} (ID: {loc_id})")
                variants = self.generate_variants(location)
                location_query = f"({' OR '.join(variants)})"
                
                BUCKETS = [
                    ("Historical", "2021-01-01", "2023-12-31"),
                    ("Recent", "2024-01-01", "2026-12-31")
                ]

                for theme_name, theme_query in THEMES.items():
                    # Target: 3 per theme per loc (2 Recent, 1 Historical)
                    for bucket_label, start_date, end_date in BUCKETS:
                        target_for_this_bucket = 1 if bucket_label == "Historical" else 2
                        
                        full_query = f'{location_query} Hyderabad ({theme_query}) after:{start_date} before:{end_date}'
                        rss_url = f"https://news.google.com/rss/search?q={quote_plus(full_query)}&hl=en-IN&gl=IN&ceid=IN:en"
                        
                        # Browser-like headers for RSS fetch
                        import requests
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
                        
                        try:
                            resp = requests.get(rss_url, headers=headers, timeout=15)
                            feed = feedparser.parse(resp.content)
                        except: continue

                        if not feed or not feed.entries: continue
                        
                        success_count = 0
                        for entry in feed.entries:
                            if success_count >= target_for_this_bucket: break
                            
                            try:
                                await page.goto(entry.link, wait_until="load", timeout=15000)
                                if "google.com" in page.url: 
                                    await page.wait_for_url(lambda u: "google.com" not in u, timeout=8000)
                                
                                final_url = page.url
                                content_html = await page.content()
                                
                                soup = BeautifulSoup(content_html, 'html.parser')
                                for s in soup(['script', 'style', 'nav', 'footer', 'header']): s.decompose()
                                text = ' '.join(soup.get_text().split())[:5000]
                                
                                if len(text) < 300: continue

                                source = entry.source.title if hasattr(entry, 'source') else 'News'
                                pub_at = entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                now_scraped = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                # Append to CSV
                                with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerow([loc_id, location, source, final_url, text, pub_at, theme_name, now_scraped])
                                
                                success_count += 1
                                print(f"      ✅ Saved Article: {entry.title[:50]}...")
                                time.sleep(random.uniform(1, 3))
                            except Exception as e: 
                                pass

                        time.sleep(random.uniform(5, 8))

            await browser.close()
            print(f"\n✨ Scraping complete. Data saved to: {self.output_file}")

if __name__ == "__main__":
    # FULL LIST: All remaining Hyderabad locations starting from Kajaguda (ID: 117)
    # This covers everything left in the database (IDs 117 to 262)
    LOCS_TO_SCRAPE = [
        (117, 'Kajaguda'), (118, 'Kalyan Nagar'), (119, 'Kamalanagar'), (121, 'Kandawada'),
        (122, 'Kandlakoya'), (123, 'Kandukur'), (124, 'Kapra'), (125, 'Karmanghat'),
        (126, 'Kavadiguda'), (127, 'Keesara'), (128, 'Khajaguda'), (129, 'Kismatpur'),
        (132, 'Kokapet'), (133, 'Kollur'), (134, 'Kompally'), (135, 'Kongara Kalan'),
        (137, 'Kothaguda'), (138, 'Kothapet'), (139, 'Kothur'), (140, 'Kowkur'),
        (141, 'Krishnareddypet'), (142, 'LB Nagar'), (144, 'Lakdikapool'), (145, 'Laxmiguda'),
        (146, 'Mokila'), (147, 'Madeenaguda'), (148, 'Maheshwaram'), (149, 'Malkajgiri'),
        (150, 'Mallampet'), (151, 'Mallapur'), (152, 'Mamidipally'), (153, 'Manchirevula'),
        (154, 'Mangalpalli'), (155, 'Manikonda'), (156, 'Manneguda'), (157, 'Mansanpally'),
        (158, 'Mansoorabad'), (159, 'Medchal'), (160, 'Medipally'), (161, 'Meerpet'),
        (162, 'Mehdipatnam'), (163, 'Miyapur'), (165, 'Moosapet'), (166, 'Moti Nagar'),
        (167, 'Moula Ali'), (168, 'Muthangi'), (170, 'Nacharam'), (171, 'Nadergul'),
        (172, 'Nagaram'), (173, 'Nagole'), (174, 'Nallagandla'), (176, 'Nallakunta'),
        (177, 'Narapally'), (178, 'Narsingi'), (179, 'Neknampur'), (180, 'Neopolis'),
        (181, 'Nizampet'), (184, 'Osman Nagar'), (186, 'Padmarao Nagar'), (187, 'Palgutta'),
        (188, 'Patancheru'), (189, 'Patancheruvu'), (190, 'Pati, Kollur'), (191, 'Patighanpur'),
        (192, 'Peeramcheruvu'), (193, 'Peeranchuruvu'), (194, 'Peerzadiguda'), (195, 'Pocharam'),
        (196, 'Podur'), (197, 'Pragathi Nagar'), (198, 'Puppalaguda'), (199, 'Puppalguda'),
        (200, 'Quthbullapur'), (202, 'Rajendra Nagar'), (203, 'Rampally'), (204, 'Rudraram'),
        (206, 'Saidabad'), (207, 'Sainikpuri'), (208, 'Sanath Nagar'), (211, 'Secunderabad'),
        (213, 'Serilingampally'), (215, 'Shadnagar'), (216, 'Shaikpet'), (217, 'Shamirpet'),
        (218, 'Shamshabad'), (219, 'Shamsheergunj'), (220, 'Shankarpally'), (221, 'Somajiguda'),
        (222, 'Suchitra'), (223, 'Suraram'), (224, 'Tellapur'), (225, 'Tarnaka'),
        (228, 'Thumkunta'), (229, 'Toroor'), (230, 'Tukkuguda'), (231, 'Turkapally'),
        (232, 'Turkayamjal'), (233, 'Uppal'), (234, 'Uppal Bhagath'), (236, 'Velimela'),
        (238, 'Yamnampet'), (239, 'Yapral'), (242, 'Yousufguda'), (243, 'gourelly'),
        (249, 'Hyderabad Average'), (250, 'Raviryal'), (251, 'Gagillapur'), (252, 'Lingampally'),
        (253, 'Shilpa Hills'), (254, 'Ramachandrapuram'), (255, 'Konapur'), (256, 'Amberpet'),
        (257, 'Dollar Hill'), (258, 'Punjagutta'), (259, 'Sirigiripuram'), (260, 'Depalle'),
        (261, 'Machirevula'), (262, 'Velmala')
    ]
    
    scraper = PortableScraperCSV()
    asyncio.run(scraper.run(LOCS_TO_SCRAPE))
