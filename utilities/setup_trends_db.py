"""
Recreate price_trends table with proper schema for professional analytics.
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

# Drop existing table
cur.execute("DROP TABLE IF EXISTS price_trends CASCADE")

# Create new sophisticated schema
cur.execute("""
    CREATE TABLE price_trends (
        id SERIAL PRIMARY KEY,
        location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
        trend_date DATE NOT NULL,
        quarter VARCHAR(10) NOT NULL,
        average_price DECIMAL(10, 2),
        min_price DECIMAL(10, 2),
        max_price DECIMAL(10, 2),
        data_points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT unique_trend UNIQUE (location_id, quarter)
    );
    
    CREATE INDEX idx_price_trends_loc ON price_trends(location_id);
    CREATE INDEX idx_price_trends_date ON price_trends(trend_date);
""")

conn.commit()
cur.close()
conn.close()

print("✅ Recreated price_trends table successfully.")
