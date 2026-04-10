
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
        """Connect to Supabase PostgreSQL database"""
        # Parse Supabase URL to get connection details
        supabase_url = os.getenv("SUPABASE_URL")
        
        if supabase_url:
            # Extract project ref from Supabase URL
            # Format: https://PROJECT_REF.supabase.co
            project_ref = supabase_url.split("//")[1].split(".")[0]
            db_host = f"db.{project_ref}.supabase.co"
            
            # Get Supabase database password
            db_password = os.getenv("SUPABASE_DB_PASSWORD", "")
            
            if not db_password:
                print("[WARNING] SUPABASE_DB_PASSWORD not found in .env")
                print("[INFO] Please add SUPABASE_DB_PASSWORD to your .env file")
                print("[INFO] You can find it in Supabase Dashboard > Settings > Database")
                raise ValueError("Missing SUPABASE_DB_PASSWORD")
            
            print(f"[CONNECT] Connecting to Supabase PostgreSQL...")
            print(f"[INFO] Host: {db_host}")
            
            self.conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password=db_password,
                host=db_host,
                port=5432
            )
        else:
            # Fallback to local database
            print("[CONNECT] Connecting to local PostgreSQL...")
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "post@123"),
                host=os.getenv("DB_HOST", "localhost"),
                port=5432
            )
        
        self.cur = self.conn.cursor()
        print("[OK] Connected to database.")

    def _load_model(self):
        print(f"[LOAD] Loading Model: {MODEL_NAME}...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        print("[OK] Model Loaded.")

    def process_table(self, table_name):
        """Process sentiment for a specific table"""
        print(f"\n[RUN] Starting Sentiment Analysis on '{table_name}'...")
        
        # 1. Fetch unprocessed rows
        self.cur.execute(f"""
            SELECT id, content 
            FROM {table_name}
            WHERE sentiment_score IS NULL
        """)
        rows = self.cur.fetchall()
        total = len(rows)
        print(f"[INFO] Found {total} unprocessed records in {table_name}.")

        if total == 0:
            print(f"[SKIP] Nothing to process in {table_name}!")
            return 0

        # 2. Batch Process
        processed = 0
        for i in tqdm(range(0, total, BATCH_SIZE), desc=f"Processing {table_name}"):
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
                self.cur.executemany(f"""
                    UPDATE {table_name}
                    SET sentiment_score = %s, sentiment_label = %s, confidence = %s
                    WHERE id = %s
                """, updates)
                self.conn.commit()
                processed += len(updates)
                
            except Exception as e:
                print(f"[ERROR] Batch Error: {e}")
                self.conn.rollback()

        print(f"\n[DONE] Processed {processed}/{total} records in {table_name}.")
        return processed

    def run(self):
        """Process sentiment for both Hyderabad and Bangalore tables"""
        print("="*60)
        print("[START] Sentiment Analysis for ALL tables")
        print("="*60)
        
        total_processed = 0
        
        # Process Hyderabad articles (news_balanced_corpus_1)
        total_processed += self.process_table('news_balanced_corpus_1')
        
        # Process Bangalore articles (bangalore_news_scraper)
        total_processed += self.process_table('bangalore_news_scraper')
        
        print("\n" + "="*60)
        print(f"[COMPLETE] Total articles processed: {total_processed}")
        print("="*60)
        
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    processor = SentimentProcessor()
    processor.run()
