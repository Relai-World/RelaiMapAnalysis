
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 50)  # Truncate long text to 50 chars for readability

def show_table_sample(table_name, limit=10):
    try:
        conn = psycopg2.connect(
            dbname="real_estate_intelligence",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        
        print(f"\n\n📝 TABLE: {table_name.upper()} (Top {limit} Rows)")
        print("=" * 80)
        
        if df.empty:
            print("(Table is empty)")
        else:
            print(df.to_string(index=False))
            
        conn.close()
    except Exception as e:
        print(f"❌ Error fetching {table_name}: {e}")

if __name__ == "__main__":
    # We focus on the big 3
    show_table_sample("location_insights", 10)
    show_table_sample("processed_sentiment_data", 10)
    show_table_sample("raw_scraped_data", 10)
