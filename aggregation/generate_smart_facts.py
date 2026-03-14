import psycopg2
import os
import math
import collections
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# KEYWORDS TO TRACK
POSITIVE_KEYWORDS = ["metro", "flyover", "launch", "expansion", "growth", "new", "hiked", "demand", "tech", "park"]
NEGATIVE_KEYWORDS = ["traffic", "pollution", "water", "shortage", "delay", "protest", "crime", "dust", "congestion"]

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        sslmode='require'
    )

def generate_sentiment_summary(location_id, cur):
    # 1. Fetch recent news headlines
    cur.execute("""
        SELECT content, sentiment_label 
        FROM news_balanced_corpus 
        WHERE location_id = %s 
        ORDER BY published_at DESC 
        LIMIT 50
    """, (location_id,))
    rows = cur.fetchall()
    
    if not rows:
        return "No recent news data available to analyze sentiment."

    # 2. Count Keywords
    pos_hits = collections.defaultdict(int)
    neg_hits = collections.defaultdict(int)
    total_articles = len(rows)

    for title, label in rows:
        text = title.lower()
        if label == 'positive':
            for kw in POSITIVE_KEYWORDS:
                if kw in text: pos_hits[kw.title()] += 1
        elif label == 'negative':
            for kw in NEGATIVE_KEYWORDS:
                if kw in text: neg_hits[kw.title()] += 1

    # 3. Formulate Sentence
    top_pos = sorted(pos_hits.items(), key=lambda x: x[1], reverse=True)[:2]
    top_neg = sorted(neg_hits.items(), key=lambda x: x[1], reverse=True)[:2]

    summary = f"Based on {total_articles} recent articles. "
    
    if top_pos and top_neg:
        summary += f"Optimism around {top_pos[0][0]} mixed with {top_neg[0][0]} concerns."
    elif top_pos:
        drivers = " and ".join([p[0] for p in top_pos])
        summary += f"Positive sentiment driven by discussions on {drivers}."
    elif top_neg:
        issues = " and ".join([n[0] for n in top_neg])
        summary += f"Market caution due to reported {issues} issues."
    else:
        summary += "Balanced market view with no dominant single topic."

    return summary

def generate_growth_summary(location_id, cur):
    # Fetch Real Infra Data
    cur.execute("""
        SELECT hospitals, schools, metro, airports 
        FROM location_infrastructure 
        WHERE location_id = %s
    """, (location_id,))
    row = cur.fetchone()

    if not row:
        return "Infrastructure data is being collected."

    h, s, m, a = row
    features = []
    if m > 0: features.append("Metro connectivity")
    if h > 2: features.append("major healthcare")
    if s > 3: features.append("schooling hubs")
    if a > 0: features.append("airport access")

    if not features:
        return "Developing area with emerging infrastructure."
    
    joined = ", ".join(features)
    return f"Well-connected zone featuring {joined}."

def generate_invest_summary(location_id, cur):
    # Fetch Price Trends
    cur.execute("SELECT year, avg_price_sqft FROM price_trends WHERE location_id = %s ORDER BY year ASC", (location_id,))
    rows = cur.fetchall()

    if len(rows) < 2:
        return "Insufficient historical data to calculate appreciation trends."

    start_price = rows[0][1]
    end_price = rows[-1][1]
    years = rows[-1][0] - rows[0][0]
    
    if years > 0:
        cagr = (math.pow(end_price / start_price, 1/years) - 1) * 100
        direction = "Growth" if cagr > 0 else "Correction"
        
        if cagr > 10:
            return f"High Appreciation: +{cagr:.1f}% Annual {direction}. Strong capital gains potential."
        elif cagr > 5:
            return f"Steady Yield: {cagr:.1f}% CAGR offers a balanced risk-reward profile."
        else:
            return f"Stable Market: {cagr:.1f}% CAGR indicates value preservation over speculation."
    
    return "Market prices are stable."

def main():
    print("[RUN] Generating Smart Summaries...")
    conn = get_db()
    cur = conn.cursor()

    # Get all locations
    cur.execute("SELECT id, name FROM locations")
    locations = cur.fetchall()

    for loc in locations:
        loc_id, name = loc
        print(f"   > Processing {name}...")
        
        sent_text = generate_sentiment_summary(loc_id, cur)
        growth_text = generate_growth_summary(loc_id, cur)
        invest_text = generate_invest_summary(loc_id, cur)

        # Update DB
        cur.execute("""
            UPDATE location_insights
            SET sentiment_summary = %s,
                growth_summary = %s,
                invest_summary = %s
            WHERE location_id = %s
        """, (sent_text, growth_text, invest_text, loc_id))

    conn.commit()
    cur.close()
    conn.close()
    print("[DONE] Summaries generated and saved.")

if __name__ == "__main__":
    main()
