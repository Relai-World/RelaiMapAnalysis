
import psycopg2
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
import os
import sys

# Force UTF-8 (Still good to have even if we remove emojis)
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
MODEL_NAME = "ProsusAI/finbert"
BATCH_SIZE = 16

class SentimentProcessor:
    def __init__(self):
        self._connect_db()
        self._load_model()

    def _connect_db(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        self.cur = self.conn.cursor()

    def _load_model(self):
        print(f"[LOAD] Loading Model: {MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        print("[OK] Model Loaded.")

    def run(self):
        print("[RUN] Starting Sentiment Analysis on 'news_balanced_corpus'...")
        
        # 1. Fetch unprocessed rows
        self.cur.execute("""
            SELECT id, content 
            FROM news_balanced_corpus 
            WHERE sentiment_score IS NULL
        """)
        rows = self.cur.fetchall()
        total = len(rows)
        print(f"[INFO] Found {total} unprocessed records.")

        if total == 0:
            print("[SKIP] Nothing to process!")
            return

        # 2. Batch Process
        for i in tqdm(range(0, total, BATCH_SIZE), desc="Processing Batches"):
            batch = rows[i : i + BATCH_SIZE]
            texts = [r[1] for r in batch if r[1] and len(r[1]) > 10]
            ids = [r[0] for r in batch if r[1] and len(r[1]) > 10]
            
            if not texts: continue

            # Tokenize
            try:
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
                
                # Process Results
                updates = []
                for idx, prob in enumerate(probs):
                    neg, neu, pos = prob.tolist()
                    
                    # Score: -1 (Negative) to +1 (Positive)
                    # We treat Neutral as 0
                    score = pos - neg 
                    confidence = max(neg, neu, pos)
                    
                    label = "neutral"
                    if score > 0.05: label = "positive"
                    elif score < -0.05: label = "negative"
                    
                    updates.append((score, label, confidence, ids[idx]))

                # Bulk Update (using executemany for this batch)
                self.cur.executemany("""
                    UPDATE news_balanced_corpus
                    SET sentiment_score = %s, sentiment_label = %s, confidence = %s
                    WHERE id = %s
                """, updates)
                self.conn.commit()
                
            except Exception as e:
                print(f"[ERROR] Batch Error: {e}")
                self.conn.rollback()

        print("\n[DONE] All sentiment scores updated.")
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    processor = SentimentProcessor()
    processor.run()
