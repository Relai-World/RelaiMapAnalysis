import time
import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from datetime import datetime
from base_scraper import BaseScraper

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

session = requests.Session()
session.headers.update(HEADERS)

SEARCH_SITES = {
    "The Hindu": "https://www.thehindu.com/search/?q={query}",
    "Indian Express": "https://indianexpress.com/?s={query}",
    "Deccan Chronicle": "https://www.deccanchronicle.com/search?search={query}"
}

LOCATIONS = [
    "HITEC City",
    "Gachibowli",
    "Madhapur",
    "Kondapur",
    "Nanakramguda",
    "Financial District",
    "Kukatpally"
]

CURRENT_YEAR = datetime.now().year
START_YEAR = CURRENT_YEAR - 4


def normalize(text: str) -> str:
    """Aggressive text normalization"""
    return " ".join(text.replace("\n", " ").replace("\t", " ").split())


def smart_parse(text: str) -> str:
    """
    Parse ANY response format:
    - RSS / XML
    - HTML
    - Hybrid / broken markup
    """
    collected = []

    # Try XML first (RSS feeds, sitemaps, etc.)
    try:
        soup_xml = BeautifulSoup(text, "xml")
        for tag in soup_xml.find_all(["title", "description", "summary", "content"]):
            collected.append(tag.get_text())
    except:
        pass

    # Always try HTML (even if XML succeeded)
    soup_html = BeautifulSoup(text, "html.parser")
    for tag in soup_html.find_all(["h1", "h2", "h3", "p", "li"]):
        collected.append(tag.get_text())

    final_text = normalize(" ".join(collected))

    return final_text if len(final_text) > 120 else None


def extract_links(search_url):
    try:
        r = session.get(search_url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        links = set()
        for a in soup.select("a[href]"):
            href = a["href"]
            if href.startswith("http"):
                links.add(href)

        return list(links)
    except:
        return []


def extract_content(url):
    try:
        r = session.get(url, timeout=20)
        return smart_parse(r.text)
    except:
        return None


def main():
    print("🚀 UNIVERSAL FORMAT-AGNOSTIC SCRAPER")
    scraper = BaseScraper()

    for location in LOCATIONS:
        loc_id = scraper.get_location_id(location)
        if not loc_id:
            print(f"❌ Location missing in DB: {location}")
            continue

        print(f"\n📍 LOCATION: {location}")

        for year in range(START_YEAR, CURRENT_YEAR + 1):
            print(f"   YEAR: {year}")

            for site, url_tpl in SEARCH_SITES.items():
                query = f"{location} Hyderabad real estate {year}"
                search_url = url_tpl.format(query=query.replace(" ", "+"))

                links = extract_links(search_url)
                print(f"      {site:<22} → Links found: {len(links)}")

                inserted = 0

                for link in links:
                    content = extract_content(link)
                    if not content:
                        continue

                    if scraper.is_duplicate(content):
                        continue

                    scraper.insert_raw_data(
                        location_id=loc_id,
                        source=site,
                        url=link,
                        content=content
                    )
                    inserted += 1
                    time.sleep(0.25)

                print(f"      {site:<22} → Inserted: {inserted}")
                time.sleep(1)

    scraper.close()
    print("\n✅ SCRAPING COMPLETE")


if __name__ == "__main__":
    main()
