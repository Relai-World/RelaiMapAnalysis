import time
import requests
import warnings
from datetime import datetime
from dateutil.relativedelta import relativedelta

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

from scraper.base_scraper import BaseScraper

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# =========================================================
# CONFIG
# =========================================================
LOCATION_NAME = "Gachibowli"
QUERY = "gachibowli"
YEARS_BACK = 3
REQUEST_DELAY = 2

HEADERS = {"User-Agent": "Mozilla/5.0 (RealEstateIntelBot/Stable)"}

# =========================================================
# SELENIUM SETUP
# =========================================================
def get_driver():
    caps = DesiredCapabilities.CHROME.copy()
    caps["pageLoadStrategy"] = "eager"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(
        service=service,
        options=options,
        desired_capabilities=caps
    )

# =========================================================
# GENERIC SELENIUM LINK FETCHER
# =========================================================
def fetch_links_selenium(url, domain_filter=None):
    driver = get_driver()
    driver.set_page_load_timeout(30)

    print(f"🔍 Loading: {url}")
    driver.get(url)
    time.sleep(6)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            if not domain_filter or domain_filter in href:
                links.add(href)

    print(f"   Found {len(links)} links")
    return list(links)

# =========================================================
# ARTICLE EXTRACTION
# =========================================================
def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    text = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))
    return text.strip() if text.strip() else None

def extract_date(html):
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", property="article:published_time")
    if meta and meta.get("content"):
        try:
            return datetime.fromisoformat(meta["content"].replace("Z", ""))
        except:
            pass
    return None  # optional

# =========================================================
# INGESTION LOGIC
# =========================================================
def ingest(db, links, source, location_id, cutoff):
    inserted = 0

    for url in links:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
        except:
            continue

        content = extract_content(r.text)
        if not content:
            continue

        if db.is_duplicate(content):
            continue

        article_date = extract_date(r.text)
        if article_date and article_date < cutoff:
            continue

        db.insert_raw_data(
            location_id=location_id,
            source=source,
            url=url,
            content=content
        )

        inserted += 1
        print(f"✔ {source}: Inserted {inserted}")
        time.sleep(REQUEST_DELAY)

    return inserted

# =========================================================
# MAIN
# =========================================================
def run():
    db = BaseScraper()
    location_id = db.get_location_id(LOCATION_NAME)

    if not location_id:
        print("❌ Location not found in DB")
        return

    cutoff = datetime.today() - relativedelta(years=YEARS_BACK)

    print(f"\n🚀 {LOCATION_NAME} | Selenium-only ingestion started")

    total = 0

    # ---------- THE HINDU ----------
    hindu_links = fetch_links_selenium(
        f"https://www.thehindu.com/search/?q={QUERY}",
        "thehindu.com"
    )
    total += ingest(db, hindu_links, "The Hindu", location_id, cutoff)

    # ---------- INDIAN EXPRESS ----------
    ie_links = fetch_links_selenium(
        f"https://indianexpress.com/?s={QUERY}",
        "indianexpress.com"
    )
    total += ingest(db, ie_links, "Indian Express", location_id, cutoff)

    # ---------- DECCAN CHRONICLE ----------
    dc_links = fetch_links_selenium(
        f"https://www.deccanchronicle.com/search?query={QUERY}",
        "deccanchronicle.com"
    )
    total += ingest(db, dc_links, "Deccan Chronicle", location_id, cutoff)

    # ---------- BUSINESS STANDARD ----------
    bs_links = fetch_links_selenium(
        f"https://www.business-standard.com/search?keyword={QUERY}",
        "business-standard.com"
    )
    total += ingest(db, bs_links, "Business Standard", location_id, cutoff)

    # ---------- PIB ----------
    pib_links = fetch_links_selenium(
        f"https://pib.gov.in/Search.aspx?query={QUERY}",
        "pib.gov.in"
    )
    pib_links = [l for l in pib_links if "PressReleasePage.aspx" in l]
    total += ingest(db, pib_links, "PIB", location_id, cutoff)

    db.close()

    print("\n==============================")
    print(f"TOTAL INSERTED: {total}")
    print("==============================")

# =========================================================
if __name__ == "__main__":
    run()
