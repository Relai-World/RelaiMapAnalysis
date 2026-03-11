import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432")
)
cursor = conn.cursor()

print("Recreating price_trends table...")

# Drop existing table
try:
    cursor.execute("DROP TABLE IF EXISTS price_trends CASCADE")
    conn.commit()
    print("✓ Dropped old price_trends table")
except Exception as e:
    print(f"Error dropping table: {e}")
    conn.rollback()

# Create new table with correct schema
try:
    cursor.execute("""
        CREATE TABLE price_trends (
            id SERIAL PRIMARY KEY,
            location VARCHAR(255) NOT NULL,
            year_2020 INTEGER,
            year_2021 INTEGER,
            year_2022 INTEGER,
            year_2023 INTEGER,
            year_2024 INTEGER,
            year_2025 INTEGER,
            year_2026 INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✓ Created new price_trends table with year columns")
except Exception as e:
    print(f"Error creating table: {e}")
    conn.rollback()

# Create index on location for faster lookups
try:
    cursor.execute("CREATE INDEX idx_price_trends_location ON price_trends(location)")
    conn.commit()
    print("✓ Created index on location column")
except Exception as e:
    print(f"Note: {e}")

cursor.close()
conn.close()

print("\n✓ Table recreation complete! Now run update_price_trends.py to insert data.")
