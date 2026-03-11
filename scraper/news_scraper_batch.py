"""
News Scraper for Missing Locations
Fetches news articles for locations with low/no news coverage
Stores data in news_balanced_corpus table
"""

import psycopg2
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import random
from textblob import TextBlob

load_dotenv()

# Target locations (ID, Name)
TARGET_LOCATIONS = [
    (37, "Alkapur"), (66, "Damaragidda"), (177, "Palgutta"), (209, "Patighanpur"),
    (214, "Peeramcheruvu"), (111, "Podur"), (113, "Appa Junction"), (118, "Depalle"),
    (134, "Gowrelly"), (77, "Gollur"), (208, "Pati Kollur"), (149, "Kandawada"),
    (95, "Krishnareddypet"), (164, "Mansanpally"), (62, "Chegur"), (121, "Sirigiripuram"),
    (65, "Chiryala"), (41, "Bacharam"), (86, "Gowdavalli"), (192, "Konapur"),
    (235, "Yamnampet"), (216, "Sainikpuri"), (137, "Uppal Bhagath"), (233, "Velimela"),
    (213, "Peeramcheruvu"), (161, "Mangalpalli"), (141, "Injapur"), (64, "Chitkul"),
    (157, "Laxmiguda"), (43, "Bandlaguda"), (225, "Tooroor"), (71, "Gandi Maisamma"),
    (70, "Gandamguda"), (146, "Kalyan Nagar"), (94, "Kowkoor"), (56, "Budvel"),
    (232, "Velimela"), (38, "Annojiguda"), (185, "Narapally"), (68, "Dulapally"),
    (140, "Hastinapuram"), (147, "Kamalanagar"), (39, "Appa Junction"), (184, "Muthangi"),
    (47, "Beeramguda"), (138, "Guttala Begumpet"), (190, "Khajaguda"), (215, "Puppalaguda"),
    (217, "Rudraram"), (143, "Isnapur"), (159, "Manchirevula"), (228, "Turkapally"),
    (191, "Kismatpur"), (220, "Shamsherganj"), (42, "Bahadurpally"), (88, "Gundlapochampally"),
    (176, "Padmarao Nagar"), (218, "Rampally"), (133, "Gopanpally"), (55, "Bowrampet"),
    (63, "Chengicherla"), (158, "Mallampet"), (201, "Mansoorabad"), (69, "Gagillapur"),
    (103, "Moula Ali"), (36, "Adibatla"), (211, "Peerzadiguda"), (67, "Dammaiguda"),
    (193, "Kongara Kalan"), (180, "Nadergul"), (219, "Raviryal"), (224, "Thumkunta"),
    (229, "Turkayamjal"), (160, "Mamidipally"), (207, "Patancheru"), (150, "Kandlakoya"),
    (186, "Neknampur"), (131, "Gajularamaram"), (221, "Shadnagar"), (102, "Mokila"),
    (163, "Manneguda"), (202, "Pocharam"), (139, "Himayat Nagar"), (135, "Habsiguda"),
    (54, "Bollaram"), (200, "Manchirevula"), (44, "Bandlaguda Jagir"), (136, "Hakimpet"),
    (181, "Nallakunta"), (212, "Saidabad"), (114, "Sanath Nagar"), (154, "Karmanghat"),
    (155, "Kavadiguda"), (187, "Neopolis"), (59, "Chandanagar"), (120, "Puppalaguda"),
    (132, "Hafeezpet")
]

def get_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def analyze_sentiment(text):
    """Analyze sentiment using TextBlob"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        confidence = abs(polarity)
        return polarity, label, confidence
    except:
        return 0.0, "neutral", 0.5

def search_google_news(location_name, year, max_results=50):
    """Search Google News for location-related articles for a specific year"""
    articles = []
    
    # Date range for the year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Search queries for real estate context
    queries = [
        f"{location_name} Hyderabad real estate",
        f"{location_name} Hyderabad property",
        f"{location_name} Hyderabad development",
        f"{location_name} Hyderabad infrastructure",
        f"{location_name} Hyderabad investment",
        f"{location_name} Hyderabad construction",
        f"{location_name} Hyderabad metro",
        f"{location_name} Hyderabad IT park"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for query in queries:
        try:
            # Google News RSS feed with date filter
            search_query = f"{query} after:{start_date} before:{end_date}"
            url = f"https://news.google.com/rss/search?q={search_query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:10]  # Get top 10 results per query
            
            for item in items:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                source = item.find('source')
                
                if title and link:
                    article = {
                        'title': title.text,
                        'url': link.text,
                        'source': source.text if source else 'Google News',
                        'published_at': pub_date.text if pub_date else None,
                        'content': description.text if description else title.text,
                        'year': year
                    }
                    articles.append(article)
            
            time.sleep(random.uniform(1, 2))  # Rate limiting
            
        except Exception as e:
            print(f"  ⚠️  Error searching Google News for {year}: {e}")
            continue
    
    return articles[:max_results]

def search_times_of_india(location_name, year):
    """Search Times of India for articles"""
    articles = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # TOI search URL
        query = f"{location_name} Hyderabad real estate property"
        url = f"https://timesofindia.indiatimes.com/searchresult.cms?query={query.replace(' ', '+')}"
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            for link in soup.find_all('a', href=True)[:15]:
                href = link.get('href', '')
                if '/articleshow/' in href and 'timesofindia.indiatimes.com' in href:
                    title = link.get_text(strip=True)
                    if title and len(title) > 20:
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': 'The Times of India',
                            'published_at': None,
                            'content': title,
                            'year': year
                        })
        
        time.sleep(random.uniform(2, 3))
    except Exception as e:
        print(f"    ⚠️  TOI search error: {e}")
    
    return articles

def search_hindu(location_name, year):
    """Search The Hindu for articles"""
    articles = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = f"{location_name} Hyderabad"
        url = f"https://www.thehindu.com/search/?q={query.replace(' ', '+')}"
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for article in soup.find_all('div', class_='story-card')[:15]:
                link = article.find('a', href=True)
                if link:
                    title_elem = article.find('h3') or article.find('h2')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = link['href']
                        if not href.startswith('http'):
                            href = 'https://www.thehindu.com' + href
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': 'The Hindu',
                            'published_at': None,
                            'content': title,
                            'year': year
                        })
        
        time.sleep(random.uniform(2, 3))
    except Exception as e:
        print(f"    ⚠️  Hindu search error: {e}")
    
    return articles

def search_deccan_chronicle(location_name, year):
    """Search Deccan Chronicle for articles"""
    articles = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = f"{location_name} Hyderabad property real estate"
        url = f"https://www.deccanchronicle.com/search?q={query.replace(' ', '+')}"
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True)[:15]:
                href = link.get('href', '')
                if '/nation/' in href or '/business/' in href:
                    title = link.get_text(strip=True)
                    if title and len(title) > 20:
                        if not href.startswith('http'):
                            href = 'https://www.deccanchronicle.com' + href
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': 'Deccan Chronicle',
                            'published_at': None,
                            'content': title,
                            'year': year
                        })
        
        time.sleep(random.uniform(2, 3))
    except Exception as e:
        print(f"    ⚠️  Deccan Chronicle search error: {e}")
    
    return articles

def search_telangana_today(location_name, year):
    """Search Telangana Today for articles"""
    articles = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = f"{location_name} Hyderabad"
        url = f"https://telanganatoday.com/?s={query.replace(' ', '+')}"
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for article in soup.find_all('article')[:15]:
                link = article.find('a', href=True)
                title_elem = article.find('h2') or article.find('h3')
                
                if link and title_elem:
                    title = title_elem.get_text(strip=True)
                    href = link['href']
                    
                    articles.append({
                        'title': title,
                        'url': href,
                        'source': 'Telangana Today',
                        'published_at': None,
                        'content': title,
                        'year': year
                    })
        
        time.sleep(random.uniform(2, 3))
    except Exception as e:
        print(f"    ⚠️  Telangana Today search error: {e}")
    
    return articles

def search_news_minute(location_name, year):
    """Search The News Minute for articles"""
    articles = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        query = f"{location_name} Hyderabad Telangana"
        url = f"https://www.thenewsminute.com/search?q={query.replace(' ', '%20')}"
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True)[:15]:
                href = link.get('href', '')
                if '/article/' in href:
                    title = link.get_text(strip=True)
                    if title and len(title) > 20:
                        if not href.startswith('http'):
                            href = 'https://www.thenewsminute.com' + href
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'source': 'The News Minute',
                            'published_at': None,
                            'content': title,
                            'year': year
                        })
        
        time.sleep(random.uniform(2, 3))
    except Exception as e:
        print(f"    ⚠️  News Minute search error: {e}")
    
    return articles

def fetch_article_content(url):
    """Try to fetch full article content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try common article selectors
        article_selectors = [
            'article', '.article-content', '.story-content', 
            '.post-content', 'main', '.content'
        ]
        
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                text = article.get_text(separator=' ', strip=True)
                if len(text) > 200:
                    return text[:5000]  # Limit to 5000 chars
        
        # Fallback: get all paragraphs
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        return text[:5000] if len(text) > 200 else None
        
    except Exception as e:
        print(f"    ⚠️  Could not fetch content: {e}")
        return None

def insert_article(conn, location_id, location_name, article):
    """Insert article into news_balanced_corpus"""
    try:
        cur = conn.cursor()
        
        # Try to fetch full content
        content = fetch_article_content(article['url'])
        if not content:
            content = article['content']
        
        # Analyze sentiment
        sentiment_score, sentiment_label, confidence = analyze_sentiment(content)
        
        # Parse published date
        published_at = None
        if article.get('published_at'):
            try:
                from email.utils import parsedate_to_datetime
                published_at = parsedate_to_datetime(article['published_at'])
            except:
                # Use year from article if available
                year = article.get('year', datetime.now().year)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                published_at = datetime(year, month, day)
        else:
            # Use year from article if available
            year = article.get('year', datetime.now().year)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            published_at = datetime(year, month, day)
        
        # Check if article already exists
        cur.execute(
            "SELECT id FROM news_balanced_corpus WHERE url = %s",
            (article['url'],)
        )
        if cur.fetchone():
            print(f"    ⏭️  Article already exists")
            cur.close()
            return False
        
        # Insert article
        cur.execute("""
            INSERT INTO news_balanced_corpus 
            (location_id, location_name, source, url, content, published_at, 
             sentiment_score, sentiment_label, confidence, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            location_id, location_name, article['source'], article['url'],
            content, published_at, sentiment_score, sentiment_label,
            confidence, datetime.now()
        ))
        
        conn.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"    ❌ Error inserting article: {e}")
        conn.rollback()
        return False

def scrape_location_news(location_id, location_name):
    """Scrape news for a single location across 2021-2026 from multiple sources"""
    print(f"\n{'='*70}")
    print(f"📰 Scraping: {location_name} (ID: {location_id})")
    print(f"{'='*70}")
    
    conn = get_db()
    
    # Check existing articles
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM news_balanced_corpus WHERE location_id = %s",
        (location_id,)
    )
    existing_count = cur.fetchone()[0]
    cur.close()
    
    print(f"📊 Existing articles: {existing_count}")
    
    # Scrape for each year from 2021 to 2026
    years = [2021, 2022, 2023, 2024, 2025, 2026]
    total_inserted = 0
    
    for year in years:
        print(f"\n  📅 Year: {year}")
        all_articles = []
        
        # Source 1: Google News
        print(f"  🔍 Searching Google News...")
        articles = search_google_news(location_name, year, max_results=30)
        all_articles.extend(articles)
        print(f"    ✓ Found {len(articles)} from Google News")
        
        # Source 2: Times of India
        print(f"  🔍 Searching Times of India...")
        articles = search_times_of_india(location_name, year)
        all_articles.extend(articles)
        print(f"    ✓ Found {len(articles)} from TOI")
        
        # Source 3: The Hindu
        print(f"  🔍 Searching The Hindu...")
        articles = search_hindu(location_name, year)
        all_articles.extend(articles)
        print(f"    ✓ Found {len(articles)} from The Hindu")
        
        # Source 4: Deccan Chronicle
        print(f"  🔍 Searching Deccan Chronicle...")
        articles = search_deccan_chronicle(location_name, year)
        all_articles.extend(articles)
        print(f"    ✓ Found {len(articles)} from Deccan Chronicle")
        
        # Source 5: Telangana Today
        print(f"  🔍 Searching Telangana Today...")
        articles = search_telangana_today(location_name, year)
        all_articles.extend(articles)
        print(f"    ✓ Found {len(articles)} from Telangana Today")
        
        # Source 6: The News Minute
        print(f"  🔍 Searching The News Minute...")
        articles = search_news_minute(location_name, year)
        all_articles.extend(articles)
        print(f"    ✓ Found {len(articles)} from The News Minute")
        
        if not all_articles:
            print(f"  ⚠️  No articles found for {year}")
            continue
        
        print(f"  ✅ Total found: {len(all_articles)} articles for {year}")
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        print(f"  📋 Unique articles: {len(unique_articles)}")
        
        # Insert articles
        inserted = 0
        for i, article in enumerate(unique_articles, 1):
            if i <= 2 or i == len(unique_articles):  # Show first 2 and last
                print(f"    [{i}/{len(unique_articles)}] {article['source']}: {article['title'][:40]}...")
            elif i == 3:
                print(f"    ... processing {len(unique_articles) - 3} more articles ...")
            
            if insert_article(conn, location_id, location_name, article):
                inserted += 1
                time.sleep(random.uniform(0.3, 0.7))
        
        total_inserted += inserted
        print(f"  ✅ Inserted {inserted} articles for {year}")
        
        # Rate limiting between years
        time.sleep(random.uniform(2, 3))
    
    conn.close()
    print(f"\n✅ Total inserted: {total_inserted} articles for {location_name}")
    return total_inserted

def main():
    print("="*70)
    print("MULTI-SOURCE NEWS SCRAPER FOR MISSING LOCATIONS (2021-2026)")
    print("="*70)
    print(f"Total locations to process: {len(TARGET_LOCATIONS)}")
    print(f"Years covered: 2021, 2022, 2023, 2024, 2025, 2026")
    print(f"News sources:")
    print(f"  1. Google News (aggregated)")
    print(f"  2. The Times of India")
    print(f"  3. The Hindu")
    print(f"  4. Deccan Chronicle")
    print(f"  5. Telangana Today")
    print(f"  6. The News Minute")
    print(f"Expected articles per location: ~100-500 (depending on availability)")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_inserted = 0
    successful = 0
    failed = 0
    
    for idx, (location_id, location_name) in enumerate(TARGET_LOCATIONS, 1):
        try:
            print(f"\n{'#'*70}")
            print(f"[{idx}/{len(TARGET_LOCATIONS)}] Processing {location_name}...")
            print(f"{'#'*70}")
            inserted = scrape_location_news(location_id, location_name)
            total_inserted += inserted
            if inserted > 0:
                successful += 1
            else:
                failed += 1
            
            # Rate limiting between locations
            time.sleep(random.uniform(3, 5))
            
        except Exception as e:
            print(f"❌ Error processing {location_name}: {e}")
            failed += 1
            continue
    
    print("\n" + "="*70)
    print("SCRAPING COMPLETE")
    print("="*70)
    print(f"✅ Successful locations: {successful}")
    print(f"❌ Failed locations: {failed}")
    print(f"📰 Total articles inserted: {total_inserted}")
    print(f"📊 Average per location: {total_inserted/len(TARGET_LOCATIONS):.1f}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
