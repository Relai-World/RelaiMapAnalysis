import time
import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from urllib.parse import urljoin

BASE_URL = "https://www.thehindu.com/news/cities/Hyderabad/"
SOURCE_NAME = "The Hindu"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RealEstateIntelBot/1.0)"
}

# ---------------- WEST HYDERABAD LOCATION KEYWORDS ----------------
WEST_HYD_LOCATIONS = {
    "gachibowli": "Gachibowli",
    "kondapur": "Kondapur",
    "hitech city": "HITECH City",
    "hi-tech city": "HITECH City",
    "madhapur": "Madhapur",
    "financial district": "Financial District",
    "nanakramguda": "Nanakramguda",
    "kukatpally": "Kukatpally"
}

# ---------------- LOCATION DETECTION ----------------
def detect_location(text: str):
    text = text.lower()
    for keyword, location_name in WEST_HYD_LOCATIONS.items():
        if keyword in text:
            return location_name
    return None


# ---------------- ARTICLE CONTENT FETCH ----------------
def fetch_article_content(article_url: str):
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text(strip=True) for p in paragraphs)

        return content.strip()

    except Exception as e:
        print(f"⚠️ Failed to fetch article: {article_url}")
        return None


def run():
    scraper = BaseScraper()
    print("✅ Scraping started (full article content)...")

    response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    articles = soup.find_all("h3")

    inserted_count = 0
    skipped_count = 0
    unmapped_count = 0
    failed_count = 0

    for article in articles:
        link = article.find("a")
        if not link or not link.get("href"):
            continue

        article_url = urljoin(BASE_URL, link["href"])

        article_text = fetch_article_content(article_url)

        if not article_text or len(article_text) < 200:
            failed_count += 1
            continue

        # Detect location from FULL article text
        location_name = detect_location(article_text)

        if not location_name:
            unmapped_count += 1
            continue

        location_id = scraper.get_location_id(location_name)
        if not location_id:
            print(f"⚠️ Location '{location_name}' not found in DB")
            continue

        # Duplicate check
        if scraper.is_duplicate(article_text):
            skipped_count += 1
            continue

        scraper.insert_raw_data(
            location_id=location_id,
            source=SOURCE_NAME,
            url=article_url,
            content=article_text
        )

        inserted_count += 1
        print(f"Inserted [{location_name}]: {article_url}")

        # Polite delay (important)
        time.sleep(2)

    scraper.close()

    print("\n✅ Scraping completed")
    print(f"Inserted: {inserted_count}")
    print(f"Skipped (duplicates): {skipped_count}")
    print(f"Unmapped (no location keyword): {unmapped_count}")
    print(f"Failed fetch/content: {failed_count}")


if __name__ == "__main__":
    run()
