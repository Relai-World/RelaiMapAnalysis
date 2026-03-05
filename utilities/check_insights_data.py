
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def check_insights():
    try:
        conn = psycopg2.connect(
            dbname="real_estate_intelligence",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=5432
        )
        
        with open("insights_report.txt", "w", encoding="utf-8") as f:
            f.write("\n🔍 CHECKING 'location_insights' TABLE DATA:\n")
            f.write("===========================================\n")
            df = pd.read_sql_query("SELECT * FROM location_insights ORDER BY id", conn)
            
            if df.empty:
                f.write("❌ Table is EMPTY.\n")
            else:
                f.write(df.to_string() + "\n")
                
            f.write("\n===========================================\n")
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_insights()
