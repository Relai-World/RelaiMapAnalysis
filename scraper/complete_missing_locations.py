#!/usr/bin/env python3

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import re
from collections import Counter

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class MissingLocationsScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_missing_locations(self):
        """Get list of locations that haven't been scraped yet"""
        try:
            # Get all unique locations from property data
            properties_response = self.supabase.table('unified_data_DataType_Raghu').select('areaname').execute()
            all_area_names = [prop['areaname'] for prop in properties_response.data if prop.get('areaname')]
            unique_locations = list(set(all_area_names))
            
            # Get already scraped locations
            future_dev_response = self.supabase.table('future_development_scrap').select('location_name').execute()
            scraped_locations = set([loc['location_name'] for loc in future_dev_response.data])
            
            # Find missing locations
            missing_locations = [loc for loc in unique_locations if loc not in scraped_locations]
            
            # Sort by property count (prioritize high-property locations)
            location_counts = Counter(all_area_names)
            missing_with_counts = [(loc, location_counts[loc]) for loc in missing_locations]
            missing_with_counts.sort(key=lambda x: x[1], reverse=True)
            
            print(f"📍 Found {len(missing_locations)} missing locations")
            print(f"🏆 Top 10 missing locations by property count:")
            for i, (location, count) in enumerate(missing_with_counts[:10], 1):
                print(f"   {i:2d}. {location}: {count} properties")
                
            return [loc for loc, count in missing_with_counts]
            
        except Exception as e:
            print(f"❌ Error getting missing locations: {e}")
            return []
    
    def search_news_for_location(self, location_name, max_results=20):
        """Search for news articles about future development in a specific location"""
        search_queries = [
            f"{location_name} Hyderabad future development 2023..2030",
            f"{location_name} Hyderabad infrastructure projects 2024..2030",
            f"{location_name} Hyderabad real estate development 2023..2030",
            f"{location_name} Hyderabad metro expansion 2024..2030",
            f"{location_name} Hyderabad IT park development 2023..2030"
        ]
        
        all_results = []
        
        for query in search_queries:
            try:
                # Use Google News search
                search_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
                
                response = self.session.get(search_url, timeout=10)
                if response.status_code == 200:
                    # Parse RSS feed (simplified)
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(response.content)
                        items = root.findall('.//item')
                        
                        for item in items[:5]:  # Limit per query
                            title = item.find('title')
                            link = item.find('link')
                            pub_date = item.find('pubDate')
                            
                            if title is not None and link is not None:
                                all_results.append({
                                    'title': title.text,
                                    'url': link.text,
                                    'published_date': pub_date.text if pub_date is not None else None,
                                    'query': query
                                })
                    except ET.ParseError:
                        continue
                        
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ⚠️ Search failed for query '{query}': {e}")
                continue
                
        return all_results[:max_results]
    
    def extract_article_content(self, url):
        """Extract article content from URL"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                # Simple content extraction (you might want to use newspaper3k or similar)
                content = response.text
                
                # Remove HTML tags (basic)
                import re
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                
                # Limit content length
                if len(content) > 5000:
                    content = content[:5000] + "..."
                    
                return content
            else:
                return f"Failed to fetch content (HTTP {response.status_code})"
                
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def extract_year_from_content(self, content):
        """Extract mentioned years from content"""
        if not content:
            return None
            
        # Look for years between 2023-2030
        year_pattern = r'\b(202[3-9]|2030)\b'
        years = re.findall(year_pattern, content)
        
        if years:
            # Return the most recent year mentioned
            return max(years)
        return None
    
    def save_to_database(self, location_name, articles):
        """Save scraped articles to database"""
        saved_count = 0
        
        for article in articles:
            try:
                # Extract content
                content = self.extract_article_content(article['url'])
                year_mentioned = self.extract_year_from_content(content)
                
                # Parse published date
                published_at = None
                if article.get('published_date'):
                    try:
                        from dateutil import parser
                        published_at = parser.parse(article['published_date']).isoformat()
                    except:
                        published_at = None
                
                # Insert into database
                data = {
                    'location_name': location_name,
                    'source': 'Google News Search',
                    'url': article['url'],
                    'content': content,
                    'published_at': published_at,
                    'year_mentioned': year_mentioned,
                    'scraped_at': datetime.now().isoformat()
                }
                
                response = self.supabase.table('future_development_scrap').insert(data).execute()
                saved_count += 1
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Failed to save article for {location_name}: {e}")
                continue
                
        return saved_count
    
    def scrape_missing_locations(self, max_locations=None):
        """Scrape all missing locations"""
        missing_locations = self.get_missing_locations()
        
        if not missing_locations:
            print("✅ No missing locations found!")
            return
            
        if max_locations:
            missing_locations = missing_locations[:max_locations]
            
        print(f"\n🚀 Starting to scrape {len(missing_locations)} missing locations...")
        print(f"=" * 60)
        
        total_articles = 0
        successful_locations = 0
        
        for i, location in enumerate(missing_locations, 1):
            print(f"\n[{i}/{len(missing_locations)}] Scraping: {location}")
            
            try:
                # Search for articles
                articles = self.search_news_for_location(location)
                
                if articles:
                    print(f"   📰 Found {len(articles)} articles")
                    
                    # Save to database
                    saved_count = self.save_to_database(location, articles)
                    print(f"   💾 Saved {saved_count} articles")
                    
                    total_articles += saved_count
                    successful_locations += 1
                else:
                    print(f"   ⚠️ No articles found")
                    
                # Rate limiting between locations
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error scraping {location}: {e}")
                continue
        
        print(f"\n🎉 SCRAPING COMPLETE!")
        print(f"=" * 60)
        print(f"Locations processed: {len(missing_locations)}")
        print(f"Successful locations: {successful_locations}")
        print(f"Total articles saved: {total_articles}")
        print(f"Average articles per location: {total_articles/successful_locations:.1f}" if successful_locations > 0 else "")

def main():
    scraper = MissingLocationsScraper()
    
    # Get command line argument for max locations (optional)
    max_locations = None
    if len(sys.argv) > 1:
        try:
            max_locations = int(sys.argv[1])
            print(f"🎯 Limiting to first {max_locations} locations")
        except ValueError:
            print("❌ Invalid number provided, scraping all locations")
    
    scraper.scrape_missing_locations(max_locations)

if __name__ == "__main__":
    main()