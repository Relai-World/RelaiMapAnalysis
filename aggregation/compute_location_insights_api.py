#!/usr/bin/env python3
"""
Compute location insights (growth_score, investment_score) for all locations
Uses Supabase REST API with SUPABASE_KEY
"""

import os
import requests
import math
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ---------------- HELPERS ----------------
def clamp(value, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, value))

def compute_growth_score(avg_sentiment, article_count):
    """
    Activity-Driven Growth Logic:
    1. Volume is the primary driver (80%)
    2. Sentiment acts as a modifier (20%)
    """
    if article_count == 0:
        return 0.0

    # 1. BUZZ SCORE (Logarithmic Scale)
    buzz = math.log(article_count + 1, 10)
    buzz_normalized = clamp(buzz / 3.5)

    # 2. SENTIMENT MODIFIER
    sentiment_normalized = clamp(avg_sentiment + 0.5)
    
    # 3. FINAL WEIGHTED SCORE (80% Buzz, 20% Sentiment)
    final_score = (0.8 * buzz_normalized) + (0.2 * sentiment_normalized)
    
    # Boost for high-volume hubs
    if article_count > 500:
        final_score *= 1.2

    return clamp(final_score)

def compute_investment_score(growth_score, avg_sentiment):
    """
    Investment Potential:
    - 70% Growth + 30% Sentiment
    """
    sentiment_normalized = clamp(avg_sentiment + 0.5)
    score = (0.7 * growth_score) + (0.3 * sentiment_normalized)
    return clamp(score)

# ---------------- SUPABASE API ----------------
class SupabaseAPI:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
        
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
    
    def get_all_locations(self):
        """Fetch all locations"""
        url = f"{self.url}/rest/v1/locations"
        params = {'select': 'id,name,city', 'order': 'id.asc'}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching locations: {response.status_code}")
            return []
    
    def get_location_sentiment(self, location_id):
        """Get sentiment stats for a location from both tables"""
        # Query news_balanced_corpus_1
        url1 = f"{self.url}/rest/v1/news_balanced_corpus_1"
        params1 = {
            'select': 'sentiment_score,confidence',
            'location_id': f'eq.{location_id}',
            'sentiment_score': 'not.is.null'
        }
        response1 = requests.get(url1, headers=self.headers, params=params1)
        
        # Query bangalore_news_scraper
        url2 = f"{self.url}/rest/v1/bangalore_news_scraper"
        params2 = {
            'select': 'sentiment_score,confidence',
            'location_id': f'eq.{location_id}',
            'sentiment_score': 'not.is.null'
        }
        response2 = requests.get(url2, headers=self.headers, params=params2)
        
        articles = []
        if response1.status_code == 200:
            articles.extend(response1.json())
        if response2.status_code == 200:
            articles.extend(response2.json())
        
        if not articles:
            return 0, 0.0, 0.0
        
        article_count = len(articles)
        avg_sentiment = sum(a['sentiment_score'] for a in articles) / article_count
        avg_confidence = sum(a.get('confidence', 0) for a in articles) / article_count
        
        return article_count, avg_sentiment, avg_confidence
    
    def upsert_location_insight(self, location_id, avg_sentiment, growth_score, investment_score):
        """Update or insert location insight"""
        url = f"{self.url}/rest/v1/location_insights"
        
        # Try to update first
        update_url = f"{url}?location_id=eq.{location_id}"
        body = {
            'avg_sentiment_score': float(avg_sentiment),
            'growth_score': float(growth_score),
            'investment_score': float(investment_score),
            'last_updated': datetime.now().isoformat()
        }
        
        response = requests.patch(update_url, headers=self.headers, json=body)
        
        # If no rows updated, insert new
        if response.status_code == 200 and response.text == '':
            body['location_id'] = location_id
            response = requests.post(url, headers=self.headers, json=body)
        
        return response.status_code in [200, 201, 204]

# ---------------- MAIN ----------------
def run():
    print("="*60)
    print("COMPUTING LOCATION INSIGHTS")
    print("="*60)
    
    api = SupabaseAPI()
    
    # Fetch all locations
    print("\n[1/3] Fetching all locations...")
    locations = api.get_all_locations()
    print(f"✅ Found {len(locations)} locations")
    
    # Process each location
    print("\n[2/3] Computing insights for each location...")
    
    success_count = 0
    error_count = 0
    
    for location in tqdm(locations, desc="Processing"):
        location_id = location['id']
        location_name = location['name']
        
        try:
            # Get sentiment data
            article_count, avg_sentiment, avg_confidence = api.get_location_sentiment(location_id)
            
            # Calculate scores
            growth_score = compute_growth_score(avg_sentiment, article_count)
            investment_score = compute_investment_score(growth_score, avg_sentiment)
            
            # Update database
            if api.upsert_location_insight(location_id, avg_sentiment, growth_score, investment_score):
                success_count += 1
            else:
                error_count += 1
                print(f"\n⚠️ Failed to update: {location_name}")
        
        except Exception as e:
            error_count += 1
            print(f"\n❌ Error processing {location_name}: {e}")
    
    # Summary
    print(f"\n[3/3] Complete!")
    print("="*60)
    print(f"✅ Success: {success_count}/{len(locations)} locations")
    print(f"❌ Errors: {error_count}/{len(locations)} locations")
    print("="*60)

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
