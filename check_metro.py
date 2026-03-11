import asyncio
from playwright.async_api import async_playwright
import feedparser
import os
import random
import logging
import re
import csv
from datetime import datetime
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,
format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ARTICLES_PER_THEME = 15
CSV_FILE = "news_dataset.csv"

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

class PortableScraperCSV:

    def __init__(self):

        self.csv_file = CSV_FILE
        self.processed_urls = set()

        self._init_csv()

    def _init_csv(self):

        if not os.path.exists(self.csv_file):

            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:

                writer = csv.writer(f)

                writer.writerow([
                    "location_id",
                    "location_name",
                    "source",
                    "url",
                    "content",
                    "published_at",
                    "category",
                    "scraped_at",
                    "extracted_locations"
                ])

    def save_to_csv(self, row):

        with open(self.csv_file, "a", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)

            writer.writerow(row)

    def generate_variants(self, name):

        variants = {name}

        if name in ALIASES:
            variants.update(ALIASES[name])

        return list(variants)

    def extract_location_from_content(self, content, location_variants):

        content_lower = content.lower()

        found_locations = []

        for variant in location_variants:

            if variant.lower() in content_lower:
                found_locations.append(variant)

        return found_locations

    async def fetch_google_news(self, query):

        rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"

        try:

            resp = requests.get(
                rss_url,
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=15
            )

            feed = feedparser.parse(resp.content)

            return feed.entries if feed and feed.entries else []

        except:

            return []

    async def process_theme_articles(self, page, feed_entries,
                                     loc_id, location, category,
                                     location_variants):

        added = 0
        skipped = 0

        for entry in feed_entries:

            if added >= ARTICLES_PER_THEME:
                break

            entry_url = getattr(entry, "link", None)

            if not entry_url or entry_url in self.processed_urls:

                skipped += 1
                continue

            try:

                await page.goto(entry.link,
                                wait_until="load",
                                timeout=15000)

                final_url = page.url

                if final_url in self.processed_urls:
                    skipped += 1
                    continue

                content_html = await page.content()

                soup = BeautifulSoup(content_html, "html.parser")

                for s in soup(['script', 'style', 'nav', 'footer', 'header']):
                    s.decompose()

                text = ' '.join(soup.get_text().split())[:5000]

                if len(text) < 500:

                    skipped += 1
                    continue

                extracted_locations = self.extract_location_from_content(
                    text,
                    location_variants
                )

                source = entry.source.title if hasattr(entry, 'source') else 'News'

                pub_at = entry.published if hasattr(entry, 'published') else datetime.now().isoformat()

                scraped_at = datetime.now().isoformat()

                self.save_to_csv([
                    int(loc_id),
                    str(location),
                    str(source),
                    str(final_url),
                    str(text),
                    str(pub_at),
                    str(category),
                    str(scraped_at),
                    ", ".join(extracted_locations)
                ])

                added += 1

                self.processed_urls.add(final_url)

                print(f"Saved {added}/{ARTICLES_PER_THEME}: {entry.title[:50]}")

                await asyncio.sleep(random.uniform(0.5, 1.5))

            except Exception as e:

                skipped += 1
                continue

        return added, skipped

    async def run(self, locations_data):

        async with async_playwright() as p:

            browser = await p.chromium.launch(headless=True)

            context = await browser.new_context()

            page = await context.new_page()

            for idx, (loc_id, location) in enumerate(locations_data):

                print(f"\nProcessing {location}")

                location_variants = self.generate_variants(location)

                location_query = f"({' OR '.join(location_variants)})"

                for theme_name, theme_query in THEMES.items():

                    full_query = f"{location_query} Hyderabad ({theme_query})"

                    entries = await self.fetch_google_news(full_query)

                    if not entries:
                        continue

                    await self.process_theme_articles(
                        page,
                        entries,
                        loc_id,
                        location,
                        theme_name,
                        location_variants
                    )

                    await asyncio.sleep(random.uniform(2, 4))

            await browser.close()


if __name__ == "__main__":

    LOCS_TO_SCRAPE = [

    (37,"Alkapur Main Road"), (66,"Damarigidda"), (177,"Palgutta"), (209,"Patighanpur"), (214,"Peeranchuruvu"),
(111,"Podur"), (113,"Appa Junction Peerancheru"), (118,"Depalle"), (134,"gourelly"), (77,"Gollur"),
(208,"Pati, Kollur"), (149,"Kandawada"), (95,"Krishnareddypet"), (164,"Mansanpally"), (62,"Chegur"),
(121,"Sirigiripuram"), (65,"Chiryala"), (41,"Bacharam"), (86,"Gowdavalli"), (192,"Konapur"),
(235,"Yamnampet"), (216,"Sainikpuri"), (137,"Uppal Bhagath"), (233,"Velmala"), (213,"Peeramcheruvu"),
(161,"Mangalpalli"), (141,"Injapur"), (64,"Chitkul"), (157,"Laxmiguda"), (43,"Bandlaguda-Nagole"),
(225,"Toroor"), (71,"Gandi Maisamma"), (70,"Gandamguda"), (146,"Kalyan Nagar"), (94,"Kowkur"),
(56,"Budwel"), (232,"Velimela"), (38,"Annojiguda"), (185,"Narapally"), (68,"Dulapally"),
(140,"Hastinapuram"), (147,"Kamalanagar"), (39,"Appa Junction"), (184,"Muthangi"), (47,"BEERAMGUDA"),
(138,"Guttala Begumpet"), (190,"Khajaguda"), (215,"Puppalguda"), (217,"Rudraram"), (143,"Isnapur"),
(159,"Manchirevula"), (228,"Turkapally"), (191,"Kismatpur"), (220,"Shamsheergunj"), (42,"Bahadurpally"),
(88,"Gundlapochampally"), (176,"Padmarao Nagar"), (218,"Rampally"), (133,"Gopanpally"), (55,"Bowrampet"),
(63,"Chengicherla"), (158,"Mallampet"), (201,"Mansoorabad"), (69,"Gagillapur"), (103,"Moula Ali"),
(36,"Adibatla"), (211,"Peerzadiguda"), (67,"Dammaiguda"), (193,"Kongara Kalan"), (180,"Nadergul"),
(219,"Raviryal"), (224,"Thumkunta"), (229,"Turkayamjal"), (160,"Mamidipally"), (207,"Patancheruvu"),
(150,"Kandlakoya"), (186,"Neknampur"), (131,"Gajularamaram"), (221,"Shadnagar"), (102,"Mokila"),
(163,"Manneguda"), (202,"Pocharam"), (139,"Himayat Nagar"), (135,"Habsiguda"), (54,"Bollaram"),
(200,"Machirevula"), (44,"Bandlaguda Jagir"), (136,"Hakimpet"), (181,"Nallakunta"), (212,"Saidabad"),
(114,"Sanath Nagar"), (154,"Karmanghat"), (155,"Kavadiguda"), (187,"Neopolis"), (59,"Chandanagar"),
(120,"Puppalaguda"), (132,"Hafeezpet")

]

    scraper = PortableScraperCSV()

    asyncio.run(scraper.run(LOCS_TO_SCRAPE))