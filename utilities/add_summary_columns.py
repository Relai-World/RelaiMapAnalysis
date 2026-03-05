
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_summary_columns():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        cur = conn.cursor()
        
        print("[RUN] Checking 'location_insights' table schema...")
        
        # Columns to add
        cols = [
            ("sentiment_summary", "TEXT"),
            ("growth_summary", "TEXT"),
            ("invest_summary", "TEXT")
        ]
        
        for col_name, col_type in cols:
            try:
                cur.execute(f"ALTER TABLE location_insights ADD COLUMN {col_name} {col_type};")
                print(f"[OK] Added column: {col_name}")
            except psycopg2.errors.DuplicateColumn:
                print(f"[NOTE] Column {col_name} already exists. Skipping.")
                conn.rollback()
            else:
                conn.commit()

        cur.close()
        conn.close()
        print("\n[DONE] Database schema updated successfully.")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    add_summary_columns()
