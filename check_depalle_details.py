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

print("=== DEPALLE DETAILED ANALYSIS ===\n")

# 1. Check sentiment - what news articles say
print("1. SENTIMENT (from news articles):")
cur.execute("""
    SELECT content, sentiment_score, sentiment_label
    FROM news_balanced_corpus
    WHERE location_name = 'Depalle'
    ORDER BY sentiment_score DESC
""")
articles = cur.fetchall()
print(f"   Total articles: {len(articles)}")
if articles:
    for i, (content, score, label) in enumerate(articles, 1):
        print(f"\n   Article {i}:")
        print(f"   Score: {score:.3f} ({label})")
        print(f"   Content preview: {content[:200]}...")

# 2. Check growth - infrastructure data
print("\n\n2. GROWTH (infrastructure):")
cur.execute("""
    SELECT hospitals, schools, malls, restaurants, banks, parks, metro, airports
    FROM location_infrastructure
    WHERE location_id = (SELECT id FROM locations WHERE name = 'Depalle')
""")
infra = cur.fetchone()
if infra:
    print(f"   Hospitals: {infra[0]}")
    print(f"   Schools: {infra[1]}")
    print(f"   Malls: {infra[2]}")
    print(f"   Restaurants: {infra[3]}")
    print(f"   Banks: {infra[4]}")
    print(f"   Parks: {infra[5]}")
    print(f"   Metro: {infra[6]}")
    print(f"   Airports: {infra[7]}")
else:
    print("   No infrastructure data found")

# 3. Check investment - price trends
print("\n\n3. INVESTMENT (price trends):")
cur.execute("""
    SELECT year_2020, year_2021, year_2022, year_2023, year_2024, year_2025, year_2026
    FROM price_trends
    WHERE LOWER(location) = LOWER('Depalle')
""")
prices = cur.fetchone()
if prices:
    years = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
    print("   Year | Price/sqft")
    print("   -----|------------")
    for year, price in zip(years, prices):
        if price:
            print(f"   {year} | ₹{price}")
    
    # Calculate CAGR
    if prices[0] and prices[-1]:
        cagr = (pow(prices[-1] / prices[0], 1/6) - 1) * 100
        print(f"\n   CAGR (2020-2026): {cagr:.1f}%")
else:
    print("   No price trend data found")

# 4. Check location_insights scores
print("\n\n4. COMPUTED SCORES (location_insights):")
cur.execute("""
    SELECT avg_sentiment_score, growth_score, investment_score
    FROM location_insights
    WHERE location_id = (SELECT id FROM locations WHERE name = 'Depalle')
""")
scores = cur.fetchone()
if scores:
    print(f"   Sentiment Score: {scores[0]:.3f} (raw)")
    print(f"   Growth Score: {scores[1]:.3f}")
    print(f"   Investment Score: {scores[2]:.3f}")
    print(f"\n   Displayed as:")
    print(f"   Sentiment: {((scores[0] + 1) / 2 * 100):.0f}%")
    print(f"   Growth: {scores[1] * 10:.1f}/10")
    print(f"   Investment: {scores[2] * 10:.1f}/10")

cur.close()
conn.close()
