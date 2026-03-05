
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_constraints():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432
    )
    cur = conn.cursor()
    
    # Check FKs for processed_sentiment_data
    print("Checking constraints for 'processed_sentiment_data'...")
    cur.execute("""
        SELECT
            tc.constraint_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='processed_sentiment_data';
    """)
    
    rows = cur.fetchall()
    if not rows:
        print("No foreign keys found.")
    else:
        for row in rows:
            print(f"Constraint: {row[0]}, Column: {row[1]} -> References: {row[2]}.{row[3]}")

    conn.close()

if __name__ == "__main__":
    check_constraints()
