"""
Aggregates all location trends into ID 249 ('Hyderabad Average')
"""
import psycopg2, os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

BASELINE_ID = 249

# Calculate market average per quarter
print("Calculating market baseline...")
cur.execute("""
    SELECT quarter, trend_date, AVG(average_price), MIN(min_price), MAX(max_price), SUM(data_points)
    FROM price_trends
    WHERE location_id != %s
    GROUP BY quarter, trend_date
    ORDER BY quarter ASC
""", (BASELINE_ID,))

rows = cur.fetchall()

inserted = 0
for row in rows:
    q, date, avg, mn, mx, count = row
    cur.execute("""
        INSERT INTO price_trends 
        (location_id, quarter, trend_date, average_price, min_price, max_price, data_points)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (location_id, quarter) DO UPDATE 
        SET average_price = EXCLUDED.average_price,
            min_price = EXCLUDED.min_price,
            max_price = EXCLUDED.max_price
    """, (BASELINE_ID, q, date, avg, mn, mx, count))
    inserted += 1

conn.commit()
cur.close()
conn.close()

print(f"✅ Created baseline trends for {inserted} quarters.")
