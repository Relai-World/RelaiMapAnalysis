"""Export location_insights table to CSV file."""
import psycopg2
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def export_location_insights():
    """Export location_insights table to CSV."""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        
        # Fetch all data from location_insights
        query = """
            SELECT 
                li.id,
                li.location_id,
                l.name as location_name,
                li.avg_sentiment_score,
                li.sentiment_summary,
                li.growth_score,
                li.growth_summary,
                li.investment_score,
                li.invest_summary,
                li.last_updated
            FROM location_insights li
            LEFT JOIN locations l ON l.id = li.location_id
            ORDER BY li.id
        """
        
        print("[RUN] Exporting location_insights table...")
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("❌ Table is empty!")
            return
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"location_insights_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"\n{'='*60}")
        print(f"[OK] Exported {len(df)} records to: {filename}")
        print(f"{'='*60}")
        print(f"\nSample data (first 5 rows):")
        print(df.head())
        print(f"\nColumn info:")
        print(f"  Total columns: {len(df.columns)}")
        for col in df.columns:
            null_count = df[col].isnull().sum()
            print(f"  - {col}: {null_count} nulls")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    export_location_insights()
