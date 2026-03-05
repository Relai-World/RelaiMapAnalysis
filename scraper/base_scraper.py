import psycopg2

import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

class BaseScraper:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()

    def is_duplicate(self, text):
        if not text: return True
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        self.cur.execute(
            "SELECT id FROM raw_scraped_data WHERE cleaned_content = %s OR content = %s LIMIT 1",
            (content_hash, text)
        )
        return self.cur.fetchone() is not None

    def insert_raw_data(self, location_id, source, url, content, price=None):
        try:
            # Check if URL exists to avoid duplicates (since constraint is missing)
            self.cur.execute("SELECT id FROM raw_scraped_data WHERE source_url = %s", (url,))
            if self.cur.fetchone():
                return False

            self.cur.execute(
                """
                INSERT INTO raw_scraped_data 
                (location_id, source, source_url, content, price)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (location_id, source, url, content, price)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("DB ERROR:", e)
            return False

    def get_location_id(self, location_name):
        try:
            self.cur.execute("SELECT id FROM locations WHERE name ILIKE %s", (f"%{location_name}%",))
            res = self.cur.fetchone()
            return res[0] if res else None
        except Exception as e:
            print(f"Error fetching location ID for {location_name}: {e}")
            return None

    def close(self):
        self.cur.close()
        self.conn.close()
