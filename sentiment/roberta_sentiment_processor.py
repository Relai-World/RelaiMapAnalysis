import psycopg2
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from datetime import datetime

# ---------------- CONFIG ----------------
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
DEVICE = torch.device("cpu")  # CPU-safe

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return psycopg2.connect(
        dbname="real_estate_intelligence",
        user="postgres",
        password="post@123",
        host="localhost",
        port=5432
    )

# ---------------- LOAD MODEL ----------------
print("Loading RoBERTa model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.to(DEVICE)
model.eval()
print("Model loaded.")

LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}

# ---------------- SENTIMENT FUNCTION ----------------
def analyze_sentiment(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256
    ).to(DEVICE)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=1)[0]

    score, label_idx = torch.max(probs, dim=0)

    return LABEL_MAP[label_idx.item()], float(score.item())

# ---------------- PROCESS PIPELINE ----------------
def run():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch raw records NOT yet processed
    cur.execute("""
        SELECT r.id, r.content
        FROM raw_scraped_data r
        LEFT JOIN processed_sentiment_data p
          ON r.id = p.raw_data_id
        WHERE p.raw_data_id IS NULL
    """)

    rows = cur.fetchall()
    print(f"Processing {len(rows)} new records...\n")

    for raw_id, content in tqdm(rows):
        label, confidence = analyze_sentiment(content)

        # Convert label to numeric score
        sentiment_score = (
            1.0 if label == "positive"
            else -1.0 if label == "negative"
            else 0.0
        )

        cur.execute("""
            INSERT INTO processed_sentiment_data
            (raw_data_id, sentiment_label, sentiment_score, confidence, processed_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            raw_id,
            label,
            sentiment_score,
            confidence,
            datetime.utcnow()
        ))

    conn.commit()
    cur.close()
    conn.close()

    print("\nSentiment processing completed successfully.")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    run()
