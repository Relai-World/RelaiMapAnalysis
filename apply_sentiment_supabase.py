#!/usr/bin/env python3
"""
Apply sentiment analysis to all articles in news_balanced_corpus_1 table
Uses Supabase REST API and FinBERT model
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
            raise ValueError("Missing Supabase credentials in .env")
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        self._load_model()

    def _load_model(self):
        print(f"🤖 Loading Model: {MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        print("✅ Model Loaded.")

    def fetch_unprocessed_articles(self):
        """Fetch articles without sentiment scores"""
        print("\n📥 Fetching unprocessed articles...")
        
        url = f"{self.supabase_url}/rest/v1/news_balanced_corpus_1"
        params = {
            'select': 'id,content,title',
            'sentiment_score': 'is.null',
            'order': 'id.asc'
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error fetching articles: {response.status_code}")
            return []
        
        articles = response.json()
        print(f"✅ Found {len(articles)} unprocessed articles")
        return articles

    def update_sentiment(self, article_id, score, label, confidence):
        """Update sentiment for a single article"""
        url = f"{self.supabase_url}/rest/v1/news_balanced_corpus_1?id=eq.{article_id}"
        body = {
            'sentiment_score': float(score),
            'sentiment_label': label,
            'confidence': float(confidence)
        }
        
        response = requests.patch(url, headers=self.headers, json=body)
        return response.status_code in [200, 204]

    def process_batch(self, batch):
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
                if self.update_sentiment(ids[idx], score, label, confidence):
                    success_count += 1
            
            return success_count
            
        except Exception as e:
            print(f"\n❌ Batch Error: {e}")
            return 0

    def run(self):
        print("="*60)
        print("🎯 SENTIMENT ANALYSIS - news_balanced_corpus_1")
        print("="*60)
        
        # Fetch unprocessed articles
        articles = self.fetch_unprocessed_articles()
        
        if not articles:
            print("\n✅ No articles to process!")
            return
        
        total = len(articles)
        processed = 0
        
        print(f"\n🔄 Processing {total} articles in batches of {BATCH_SIZE}...")
        
        # Process in batches
        for i in tqdm(range(0, total, BATCH_SIZE), desc="Processing"):
            batch = articles[i:i + BATCH_SIZE]
            success = self.process_batch(batch)
            processed += success
        
        print(f"\n" + "="*60)
        print(f"✅ COMPLETE!")
        print(f"   Processed: {processed}/{total} articles")
        print(f"   Success Rate: {processed/total*100:.1f}%")
        print("="*60)

if __name__ == "__main__":
    try:
        processor = SentimentProcessor()
        processor.run()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
