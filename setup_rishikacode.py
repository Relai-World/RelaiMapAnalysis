"""
Rename news_balanced_corpus to news_balanced_corpus_1
Required for rishikaCode branch compatibility
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_NAME = os.getenv("DB_NAME", "real_estate_intelligence")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "post@123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def rename_table():
    """Rename news_balanced_corpus to news_balanced_corpus_1"""
    
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    cur = conn.cursor()
    
    try:
        # Check if old table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'news_balanced_corpus'
            )
        """)
        old_exists = cur.fetchone()[0]
        
        # Check if new table already exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'news_balanced_corpus_1'
            )
        """)
        new_exists = cur.fetchone()[0]
        
        if new_exists:
            print("✅ Table 'news_balanced_corpus_1' already exists!")
            return
        
        if not old_exists:
            print("❌ Table 'news_balanced_corpus' does not exist!")
            return
        
        # Rename the table
        print("Renaming 'news_balanced_corpus' to 'news_balanced_corpus_1'...")
        cur.execute("ALTER TABLE news_balanced_corpus RENAME TO news_balanced_corpus_1")
        conn.commit()
        
        print("✅ Table renamed successfully!")
        
        # Verify row count
        cur.execute("SELECT COUNT(*) FROM news_balanced_corpus_1")
        count = cur.fetchone()[0]
        print(f"📊 Total records in news_balanced_corpus_1: {count:,}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    rename_table()
