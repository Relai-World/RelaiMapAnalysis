import time
import re
import requests
from bs4 import BeautifulSoup
from scraper.base_scraper import BaseScraper

HEADERS = {
    "User-Agent": "Mozilla/5.0 (LocationRelevanceBot/1.0)"
}

session = requests.Session()
session.headers.update(HEADERS)

SEARCH_SITES = {
    "The Hindu": "https://www.thehindu.com/search/?q={q}&page={p}",
    "Indian Express": "https://indianexpress.com/?s={q}&paged={p}",
    "Deccan Chronicle": "https://www.deccanchronicle.com/search?search={q}&page={p}"
}

PAGES = 5

# These define *location-impacting sentiment*
IMPACT_KEYWORDS = [
    "road", "metro", "traffic", "flyover",
    "infrastructure", "development", "growth",
    "real estate", "housing", "apartment",
    "office", "commercial", "it", "tech",
    "company", "startup", "jobs", "employment",
    "investment", "business",
    "hospital", "health",
    "school", "college", "education",
    "restaurant", "mall", "retail",
    "water", "electricity", "pollution",
    "crime", "flood", "safety", "civic"
]

def normalize(text):
    return " ".join(text.replace("\n", " ").split())

def extract_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

def extract_clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    texts = []

    for tag in soup.find_all(["h1", "h2", "p", "li"]):
        txt = tag.get_text(strip=True)
        if txt:
            texts.append(txt)

    return normalize(" ".join(texts))

def is_relevant(content, location):
    location_l = location.lower()
    content_l = content.lower()

    # Location must be central, not incidental
    if content_l.count(location_l) < 2:
        return False

    sentences = extract_sentences(content)

    relevant_sentences = [
        s for s in sentences
        if location_l in s.lower()
        and any(k in s.lower() for k in IMPACT_KEYWORDS)
    ]

    final_text = " ".join(relevant_sentences)
    return final_text if len(final_text) >= 300 else None

def run(location):
    print(f"\n🚀 SCRAPING RELEVANT DATA FOR: {location}")
    scraper = BaseScraper()
    loc_id = scraper.get_location_id(location)

    if not loc_id:
        print("❌ Location not found in DB")
        return

    inserted = 0

    for source, url_tpl in SEARCH_SITES.items():
        for p in range(1, PAGES + 1):
            query = f"{location} Hyderabad"
            url = url_tpl.format(q=query.replace(" ", "+"), p=p)

            try:
                r = session.get(url, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")

                links = {
                    a["href"] for a in soup.select("a[href]")
                    if a["href"].startswith("http")
                }

                for link in links:
                    try:
                        page = session.get(link, timeout=15)
                        raw_text = extract_clean_text(page.text)
                        if not raw_text:
                            continue

                        filtered = is_relevant(raw_text, location)
                        if not filtered:
                            continue

                        if scraper.is_duplicate(filtered):
                            continue

                        scraper.insert_raw_data(
                            location_id=loc_id,
                            source=source,
                            url=link,
                            content=filtered
                        )
                        inserted += 1
                        time.sleep(0.4)

                    except:
                        continue

            except:
                continue

    scraper.close()
    print(f"✅ INSERTED RELEVANT RECORDS: {inserted}")

if __name__ == "__main__":
    # CHANGE LOCATION EACH RUN
    run("Kukatpally")
