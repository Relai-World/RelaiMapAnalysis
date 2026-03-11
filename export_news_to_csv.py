import psycopg2
import csv
import os
from dotenv import load_dotenv

load_dotenv()

def export_table_to_csv():
    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "post@123")
    dbname = os.getenv("DB_NAME", "real_estate_intelligence")
    port = os.getenv("DB_PORT", "5432")
    
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        dbname=dbname,
        port=port
    )
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM news_balanced_corpus")
    rows = cur.fetchall()
    
    col_names = [desc[0] for desc in cur.description]
    
    with open("news_balanced_corpus.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(col_names)
        writer.writerows(rows)
        
    print(f"Exported {len(rows)} rows to news_balanced_corpus.csv")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    export_table_to_csv()
