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

# Count total records
cursor.execute("SELECT COUNT(*) FROM price_trends")
count = cursor.fetchone()[0]
print(f"Total records in price_trends: {count}")

# Show sample data
cursor.execute("SELECT location, year_2020, year_2021, year_2026 FROM price_trends LIMIT 10")
print("\nSample data:")
print("Location | 2020 | 2021 | 2026")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]:<20} | {row[1]:<6} | {row[2]:<6} | {row[3]}")

cursor.close()
conn.close()
