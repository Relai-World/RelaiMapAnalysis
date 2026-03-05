
import requests
import feedparser
import base64
import functools
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

def decode_google_news_url(url):
    print(f"Original: {url}")
    try:
        # 1. Base64 Check
        # Google News URLs often have a long base64 string
        # https://news.google.com/rss/articles/CBMi...
        
        # 2. Requests Follow
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        
        resp = session.get(url, timeout=10, allow_redirects=True)
        final_url = resp.url
        print(f"Resolved: {final_url}")
        
        # Check content if it's still a redirect page
        if "google.com" in final_url:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Look for "Opening..." or "Redirecting..."
            print(f"Still Google URL. Title: {soup.title.string if soup.title else 'No Title'}")
            
            links = soup.find_all('a')
            for a in links:
                print(f"Found link: {a.get('href')}")

        return final_url
    except Exception as e:
        print(f"Error: {e}")
        return url

def test_feed():
    rss_url = "https://news.google.com/rss/search?q=Gachibowli+Hyderabad+real+estate&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        print("No entries found!")
        return

    print(f"Found {len(feed.entries)} entries. Testing first 5...")
    for i, entry in enumerate(feed.entries[:5]):
        print(f"\n--- Entry {i+1} ---")
        print(f"Title: {entry.title}")
        url = entry.link
        decode_google_news_url(url)

if __name__ == "__main__":
    test_feed()
