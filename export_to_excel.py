import psycopg2
import pandas as pd

conn = psycopg2.connect(
    dbname="real_estate_intelligence",
    user="postgres",
    password="post@123",
    host="localhost",
    port="5432"
)

query = """
SELECT
    r.id,
    l.name AS location,
    r.source,
    r.source_url,
    r.content
FROM raw_scraped_data r
JOIN locations l ON r.location_id = l.id
"""

df = pd.read_sql(query, conn)
conn.close()

# Clean bad characters
df["content"] = df["content"].astype(str).str.replace(r'[\x00-\x1F\x7F]', '', regex=True)

# Export
df.to_excel(
    "C:/Users/gudde/OneDrive/Desktop/Final/raw_scraped_data.xlsx",
    index=False,
    engine="openpyxl"
)

print("✅ FULL DATA EXPORTED SUCCESSFULLY")
print("Rows:", len(df))
