import time
import requests
import warnings
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper

warnings.filterwarnings("ignore")

# ===============================
# CONFIG
# ===============================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (LocationScraper/1.0)"
}

session = requests.Session()
session.headers.update(HEADERS)

SEARCH_SITES = {
    "The Hindu": {
        "search": "https://www.thehindu.com/search/?q={q}&page={p}",
        "pages": 5,
        "rss": ["https://www.thehindu.com/feeder/default.rss"]
    },
    "Indian Express": {
        "search": "https://indianexpress.com/?s={q}&paged={p}",
        "pages": 5,
        "rss": ["https://indianexpress.com/feed/"]
    },
    "Deccan Chronicle": {
        "search": "https://www.deccanchronicle.com/search?search={q}&page={p}",
        "pages": 2,
        "rss": ["https://www.deccanchronicle.com/rss.xml"]
    }
}

# ===============================
# HELPERS
# ===============================

def normalize(text: str) -> str:
    return " ".join(text.replace("\n", " ").replace("\t", " ").split())

def extract_text(raw_html: str):
    """
    Universal parser:
    - Works for HTML
    - Works for RSS
    - No XML dependency
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    texts = []
    for tag in soup.find_all(
        ["title", "h1", "h2", "p", "li", "description", "summary"]
    ):
        texts.append(tag.get_text())

    final = normalize(" ".join(texts))
    return final if final.strip() else None

def extract_links_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    return {
        a["href"]
        for a in soup.select("a[href]")
        if a["href"].startswith("http")
    }

def extract_links_rss(xml: str):
    soup = BeautifulSoup(xml, "html.parser")
    links = set()

    for link in soup.find_all("link"):
        url = link.get_text().strip()
        if url.startswith("http"):
            links.add(url)

    return links

# ===============================
# DISCOVERY
# ===============================

def discover_links(location: str):
    found = set()
    query = location.replace(" ", "+")

    for source, cfg in SEARCH_SITES.items():

        # Search pages
        for page in range(1, cfg["pages"] + 1):
            try:
                url = cfg["search"].format(q=query, p=page)
                r = session.get(url, timeout=15)

                for link in extract_links_html(r.text):
                    found.add((source, link))

                time.sleep(0.3)
            except:
                pass

        # RSS feeds
        for rss_url in cfg["rss"]:
            try:
                r = session.get(rss_url, timeout=15)
                for link in extract_links_rss(r.text):
                    found.add((source, link))
            except:
                pass

    return list(found)

# ===============================
# MAIN
# ===============================

def run():
    LOCATION = "Kukatpally"
    print(f"\n🚀 SCRAPING LOCATION: {LOCATION}")

    scraper = BaseScraper()
    loc_id = scraper.get_location_id(LOCATION)

    if not loc_id:
        print("❌ Location not found in DB")
        return

    links = discover_links(LOCATION)
    print(f"🔗 Total links discovered: {len(links)}")

    fetched = 0
    inserted = 0
    empty = 0

    for source, url in links:
        try:
            r = session.get(url, timeout=15)
            fetched += 1

            content = extract_text(r.text)
            if not content:
                empty += 1
                continue

            if scraper.insert_raw_data(
                location_id=loc_id,
                source=source,
                url=url,
                content=content
            ):
                inserted += 1

            time.sleep(0.2)

        except Exception as e:
            print("FETCH ERROR:", e)

    print("📊 FETCHED:", fetched)
    print("📊 EMPTY CONTENT:", empty)
    print("📊 INSERTED:", inserted)

    scraper.close()
    print("✅ DONE")

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    run()
