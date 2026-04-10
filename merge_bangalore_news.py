#!/usr/bin/env python3
"""
Merge bangalore_news_scraper articles into news_balanced_corpus_1 table
"""

import os
import requests
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

def merge_news_tables():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    print("="*60)
    print("🔄 MERGING bangalore_news_scraper → news_balanced_corpus_1")
    print("="*60)
    
    # Step 1: Fetch all articles from bangalore_news_scraper
    print("\n📥 Fetching articles from bangalore_news_scraper...")
    
    url_source = f"{supabase_url}/rest/v1/bangalore_news_scraper"
    params = {'select': '*', 'order': 'id.asc'}
    
    response = requests.get(url_source, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error fetching articles: {response.status_code}")
        return
    
    articles = response.json()
    total = len(articles)
    print(f"✅ Found {total} articles to merge")
    
    if total == 0:
        print("⚠️ No articles to merge!")
        return
    
    # Step 2: Insert articles into news_balanced_corpus_1
    print(f"\n📤 Inserting articles into news_balanced_corpus_1...")
    
    url_target = f"{supabase_url}/rest/v1/news_balanced_corpus_1"
    
    success_count = 0
    error_count = 0
    batch_size = 100
    
    for i in tqdm(range(0, total, batch_size), desc="Inserting"):
        batch = articles[i:i + batch_size]
        
        # Prepare batch data
        batch_data = []
        for article in batch:
            # Map fields from bangalore_news_scraper to news_balanced_corpus_1
            record = {
                'location_id': article.get('location_id'),
                'location_name': article.get('location_name'),
                'source': article.get('source'),
                'url': article.get('url'),
                'content': article.get('content'),
                'published_at': article.get('published_at'),
                'category': article.get('category'),
                'scraped_at': article.get('scraped_at'),
                'sentiment_score': None,  # Will be filled by sentiment analysis
                'sentiment_label': None,
                'confidence': None
            }
            batch_data.append(record)
        
        # Insert batch
        try:
            response = requests.post(url_target, headers=headers, json=batch_data)
            
            if response.status_code in [200, 201]:
                success_count += len(batch)
            else:
                error_count += len(batch)
                print(f"\n⚠️ Batch error: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            error_count += len(batch)
            print(f"\n❌ Exception: {e}")
    
    # Step 3: Verify
    print(f"\n" + "="*60)
    print(f"✅ MERGE COMPLETE!")
    print(f"   Success: {success_count}/{total} articles")
    print(f"   Errors: {error_count}/{total} articles")
    print(f"   Success Rate: {success_count/total*100:.1f}%")
    
    # Check final count
    print(f"\n🔍 Verifying news_balanced_corpus_1 table...")
    response = requests.head(url_target, headers=headers, params={'select': 'id'})
    if 'content-range' in response.headers:
        content_range = response.headers['content-range']
        if '/' in content_range:
            final_count = content_range.split('/')[-1]
            print(f"✅ Final count in news_balanced_corpus_1: {final_count} articles")
    
    print("="*60)

if __name__ == "__main__":
    try:
        merge_news_tables()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
