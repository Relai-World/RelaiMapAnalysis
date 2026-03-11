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

print("=== SENTIMENT SCORE DISTRIBUTION ===\n")

# Check raw sentiment scores from news_balanced_corpus
cur.execute("""
    SELECT 
        location_name,
        COUNT(*) as article_count,
        ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment,
        ROUND(MIN(sentiment_score)::numeric, 3) as min_sentiment,
        ROUND(MAX(sentiment_score)::numeric, 3) as max_sentiment
    FROM news_balanced_corpus
    WHERE sentiment_score IS NOT NULL
    GROUP BY location_name
    ORDER BY avg_sentiment DESC
    LIMIT 20
""")

print("Top 20 locations by average sentiment (from news_balanced_corpus):")
print(f"{'Location':<25} {'Articles':<10} {'Avg':<10} {'Min':<10} {'Max'}")
print("-" * 75)
for row in cur.fetchall():
    print(f"{row[0]:<25} {row[1]:<10} {row[2]:<10} {row[3]:<10} {row[4]}")

# Check location_insights table
print("\n=== LOCATION INSIGHTS TABLE ===\n")
cur.execute("""
    SELECT 
        l.name,
        li.avg_sentiment_score,
        li.growth_score,
        li.investment_score
    FROM location_insights li
    JOIN locations l ON l.id = li.location_id
    ORDER BY li.avg_sentiment_score DESC
    LIMIT 20
""")

print("Top 20 locations by sentiment (from location_insights):")
print(f"{'Location':<25} {'Sentiment':<15} {'Growth':<15} {'Investment'}")
print("-" * 75)
for row in cur.fetchall():
    print(f"{row[0]:<25} {row[1]:<15} {row[2]:<15} {row[3]}")

# Check the sentiment score range
print("\n=== SENTIMENT SCORE STATISTICS ===\n")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        ROUND(AVG(sentiment_score)::numeric, 3) as avg,
        ROUND(MIN(sentiment_score)::numeric, 3) as min,
        ROUND(MAX(sentiment_score)::numeric, 3) as max,
        ROUND(STDDEV(sentiment_score)::numeric, 3) as stddev
    FROM news_balanced_corpus
    WHERE sentiment_score IS NOT NULL
""")

row = cur.fetchone()
print(f"Total articles: {row[0]}")
print(f"Average sentiment: {row[1]}")
print(f"Min sentiment: {row[2]}")
print(f"Max sentiment: {row[3]}")
print(f"Std deviation: {row[4]}")

cur.close()
conn.close()
