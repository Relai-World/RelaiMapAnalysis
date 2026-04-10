#!/usr/bin/env python3
"""
Get exact schema of both tables by trying to insert a test record
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
}

print("🔍 Getting table schemas...")
print("="*60)

# Get bangalore_news_scraper schema
print("\n📋 bangalore_news_scraper columns:")
url1 = f"{supabase_url}/rest/v1/bangalore_news_scraper"
params1 = {'select': '*', 'limit': '1'}
response1 = requests.get(url1, headers=headers, params=params1)

if response1.status_code == 200:
    data1 = response1.json()
    if data1:
        for i, key in enumerate(data1[0].keys(), 1):
            print(f"   {i}. {key}")

# Get news_balanced_corpus_1 schema
print("\n📋 news_balanced_corpus_1 columns:")
url2 = f"{supabase_url}/rest/v1/news_balanced_corpus_1"
params2 = {'select': '*', 'limit': '1'}
response2 = requests.get(url2, headers=headers, params=params2)

if response2.status_code == 200:
    data2 = response2.json()
    if data2:
        for i, key in enumerate(data2[0].keys(), 1):
            print(f"   {i}. {key}")
    else:
        print("   (Table is empty, trying to get schema from error...)")
        # Try inserting empty record to see required fields
        test_data = {}
        response_test = requests.post(url2, headers=headers, json=test_data)
        print(f"   Error response: {response_test.text}")

print("\n" + "="*60)
