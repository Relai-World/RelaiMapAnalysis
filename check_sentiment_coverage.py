import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'post@123'),
    dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
    port=os.getenv('DB_PORT', '5432'),
    sslmode='require' if os.getenv('DB_HOST') != 'localhost' else 'prefer'
)

cur = conn.cursor()

print("=== SENTIMENT ANALYSIS COVERAGE ===\n")

# Total articles
cur.execute("SELECT COUNT(*) FROM news_balanced_corpus")
total = cur.fetchone()[0]
print(f"Total articles in corpus: {total}")

# Articles with sentiment
cur.execute("SELECT COUNT(*) FROM news_balanced_corpus WHERE sentiment_score IS NOT NULL")
with_sentiment = cur.fetchone()[0]
print(f"Articles with sentiment: {with_sentiment}")
print(f"Coverage: {(with_sentiment/total*100):.1f}%\n")

# Articles without sentiment
cur.execute("SELECT COUNT(*) FROM news_balanced_corpus WHERE sentiment_score IS NULL")
without_sentiment = cur.fetchone()[0]
print(f"Articles WITHOUT sentiment: {without_sentiment}\n")

# Breakdown by location
print("=== SENTIMENT BY LOCATION ===")
cur.execute("""
    SELECT 
        location_name,
        COUNT(*) as total_articles,
        COUNT(sentiment_score) as with_sentiment,
        COUNT(*) - COUNT(sentiment_score) as without_sentiment,
        ROUND(COUNT(sentiment_score)::numeric / COUNT(*) * 100, 1) as coverage_pct
    FROM news_balanced_corpus
    GROUP BY location_name
    ORDER BY total_articles DESC
    LIMIT 20
""")

print(f"{'Location':<25} {'Total':<8} {'With':<8} {'Without':<10} {'Coverage'}")
print("-" * 70)
for row in cur.fetchall():
    loc, total, with_s, without_s, pct = row
    print(f"{loc:<25} {total:<8} {with_s:<8} {without_s:<10} {pct}%")

# Check if any locations have 0 sentiment
print("\n=== LOCATIONS WITH NO SENTIMENT DATA ===")
cur.execute("""
    SELECT location_name, COUNT(*) as article_count
    FROM news_balanced_corpus
    WHERE sentiment_score IS NULL
    GROUP BY location_name
    HAVING COUNT(*) > 0
    ORDER BY article_count DESC
    LIMIT 10
""")

rows = cur.fetchall()
if rows:
    print(f"{'Location':<25} {'Articles without sentiment'}")
    print("-" * 50)
    for row in rows:
        print(f"{row[0]:<25} {row[1]}")
else:
    print("All locations have sentiment data!")

cur.close()
conn.close()
