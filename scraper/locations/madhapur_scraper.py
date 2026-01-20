import time
import requests
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from scraper.base_scraper import BaseScraper

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

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

def normalize(text):
    return " ".join(text.replace("\n", " ").replace("\t", " ").split())

def extract_text(raw):
    texts = []

    soup_xml = BeautifulSoup(raw, "xml")
    for t in soup_xml.find_all(["title", "description", "summary", "content", "encoded"]):
        texts.append(t.get_text())

    soup_html = BeautifulSoup(raw, "html.parser")
    for t in soup_html.find_all(["title", "h1", "h2", "p", "li"]):
        texts.append(t.get_text())

    final = normalize(" ".join(texts))
    return final if final.strip() else None

def extract_links_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return {a["href"] for a in soup.select("a[href]") if a["href"].startswith("http")}

def extract_links_rss(xml):
    soup = BeautifulSoup(xml, "xml")
    links = set()
    for item in soup.find_all(["item", "entry"]):
        link = item.find("link")
        if link and link.get_text().startswith("http"):
            links.add(link.get_text())
    return links

def discover_links(location):
    found = set()
    q = location.replace(" ", "+")

    for source, cfg in SEARCH_SITES.items():
        for p in range(1, cfg["pages"] + 1):
            try:
                url = cfg["search"].format(q=q, p=p)
                r = session.get(url, timeout=15)
                for l in extract_links_html(r.text):
                    found.add((source, l))
                time.sleep(0.3)
            except:
                pass

        for rss in cfg["rss"]:
            try:
                r = session.get(rss, timeout=15)
                for l in extract_links_rss(r.text):
                    found.add((source, l))
            except:
                pass

    return list(found)

def run():
    LOCATION = "Madhapur"
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

            if scraper.insert_raw_data(loc_id, source, url, content):
                inserted += 1

            time.sleep(0.2)
        except Exception as e:
            print("FETCH ERROR:", e)

    print("📊 FETCHED:", fetched)
    print("📊 EMPTY CONTENT:", empty)
    print("📊 INSERTED:", inserted)

    scraper.close()
    print("✅ DONE")

if __name__ == "__main__":
    run()
