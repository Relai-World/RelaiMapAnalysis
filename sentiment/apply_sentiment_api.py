#!/usr/bin/env python3
"""
Apply sentiment analysis using Supabase REST API
Works with SUPABASE_URL and SUPABASE_KEY from .env
"""

import os
import requests
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
MODEL_NAME = "ProsusAI/finbert"
BATCH_SIZE = 16

class SentimentProcessor:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        self._load_model()

    def _load_model(self):
        print(f"[LOAD] Loading Model: {MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        print("[OK] Model Loaded.")

    def fetch_unprocessed(self, table_name):
        """Fetch ALL articles without sentiment scores (handles pagination)"""
        print(f"\n[FETCH] Getting unprocessed articles from {table_name}...")
        
        all_articles = []
        offset = 0
        limit = 1000
        
        while True:
            url = f"{self.supabase_url}/rest/v1/{table_name}"
            params = {
                'select': 'id,content',
                'sentiment_score': 'is.null',
                'order': 'id.asc',
                'limit': limit,
                'offset': offset
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch: {response.status_code}")
                break
            
            articles = response.json()
            
            if not articles:
                break
            
            all_articles.extend(articles)
            print(f"[INFO] Fetched {len(articles)} articles (total: {len(all_articles)})")
            
            if len(articles) < limit:
                break
            
            offset += limit
        
        print(f"[INFO] Total unprocessed articles: {len(all_articles)}")
        return all_articles

    def update_sentiment(self, table_name, article_id, score, label, confidence):
        """Update sentiment for a single article"""
        url = f"{self.supabase_url}/rest/v1/{table_name}?id=eq.{article_id}"
        body = {
            'sentiment_score': float(score),
            'sentiment_label': label,
            'confidence': float(confidence)
        }
        
        response = requests.patch(url, headers=self.headers, json=body)
        return response.status_code in [200, 204]

    def process_batch(self, table_name, batch):
        """Process a batch of articles"""
        # Filter valid texts
        valid_items = [(item['id'], item['content']) for item in batch 
                       if item.get('content') and len(item['content']) > 10]
        
        if not valid_items:
            return 0
        
        ids = [item[0] for item in valid_items]
        texts = [item[1] for item in valid_items]
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Process results and update
            success_count = 0
            for idx, prob in enumerate(probs):
                neg, neu, pos = prob.tolist()
                
                # Score: -1 (Negative) to +1 (Positive)
                score = pos - neg
                confidence = max(neg, neu, pos)
                
                label = "neutral"
                if score > 0.05:
                    label = "positive"
                elif score < -0.05:
                    label = "negative"
                
                # Update in Supabase
                if self.update_sentiment(table_name, ids[idx], score, label, confidence):
                    success_count += 1
            
            return success_count
            
        except Exception as e:
            print(f"\n[ERROR] Batch Error: {e}")
            return 0

    def process_table(self, table_name):
        """Process all unprocessed articles in a table"""
        print(f"\n{'='*60}")
        print(f"[RUN] Processing table: {table_name}")
        print(f"{'='*60}")
        
        # Fetch unprocessed articles
        articles = self.fetch_unprocessed(table_name)
        
        if not articles:
            print(f"[SKIP] No articles to process in {table_name}!")
            return 0
        
        total = len(articles)
        processed = 0
        
        print(f"\n[PROCESS] Processing {total} articles in batches of {BATCH_SIZE}...")
        
        # Process in batches
        for i in tqdm(range(0, total, BATCH_SIZE), desc=f"{table_name}"):
            batch = articles[i:i + BATCH_SIZE]
            success = self.process_batch(table_name, batch)
            processed += success
        
        print(f"\n[DONE] Processed {processed}/{total} articles in {table_name}")
        return processed

    def run(self):
        """Process both tables"""
        print("="*60)
        print("[START] Sentiment Analysis for ALL tables")
        print("="*60)
        
        total_processed = 0
        
        # Process Hyderabad articles
        total_processed += self.process_table('news_balanced_corpus_1')
        
        # Process Bangalore articles
        total_processed += self.process_table('bangalore_news_scraper')
        
        print(f"\n{'='*60}")
        print(f"[COMPLETE] Total articles processed: {total_processed}")
        print(f"{'='*60}")

if __name__ == "__main__":
    try:
        processor = SentimentProcessor()
        processor.run()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
