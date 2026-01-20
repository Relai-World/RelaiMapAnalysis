import psycopg2
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        dbname="real_estate_intelligence",
        user="postgres",
        password="post@123",
        host="localhost",
        port=5432
    )

# ---------------- MODEL LOAD ----------------
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"

print("🔄 Loading sentiment model (news / media tone)...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()
print("✅ Model loaded.")

# ---------------- MAIN PROCESS ----------------
def run():
    conn = get_db_connection()
    cur = conn.cursor()

    print("📥 Fetching unprocessed records...")
    cur.execute("""
        SELECT id, content
        FROM raw_scraped_data
        WHERE id NOT IN (
            SELECT raw_data_id FROM processed_sentiment_data
        )
    """)
    rows = cur.fetchall()
    total = len(rows)

    print(f"🧠 Processing {total} records...")

    if total == 0:
        print("⚠️ Nothing to process.")
        return

    results = []

    with torch.no_grad():
        for raw_id, text in tqdm(rows, mininterval=1):
            if not text or len(text.strip()) < 20:
                continue

            inputs = tokenizer(
                text,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )

            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)[0].tolist()

            # CardiffNLP label order:
            # 0 = negative, 1 = neutral, 2 = positive
            neg, neu, pos = probs

            # ---- CORRECT SENTIMENT SCORE ----
            # Balanced, unbiased, continuous [-1, +1]
            sentiment_score = pos - neg

            # Confidence = how decisive the model was
            confidence = max(probs)

            # Label (purely descriptive)
            if pos > max(neg, neu):
                sentiment_label = "positive"
            elif neg > max(pos, neu):
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

            results.append((
                int(raw_id),
                float(sentiment_score),
                float(confidence),
                sentiment_label
            ))

    if not results:
        print("⚠️ No valid records processed.")
        return

    print("💾 Writing sentiment results to database...")

    cur.executemany("""
        INSERT INTO processed_sentiment_data
            (raw_data_id, sentiment_score, confidence, sentiment_label)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (raw_data_id)
        DO NOTHING
    """, results)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Sentiment processing completed successfully.")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run()
