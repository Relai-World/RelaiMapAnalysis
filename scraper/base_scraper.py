import psycopg2

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

    def get_location_id(self, location_name):
        self.cur.execute(
            "SELECT id FROM locations WHERE LOWER(name)=LOWER(%s)",
            (location_name,)
        )
        row = self.cur.fetchone()
        return row[0] if row else None

    def insert_raw_data(self, location_id, source, url, content):
        try:
            self.cur.execute(
                """
                INSERT INTO raw_scraped_data
                (location_id, source, source_url, content)
                VALUES (%s, %s, %s, %s)
                """,
                (location_id, source, url, content)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print("DB ERROR:", e)
            return False

    def close(self):
        self.cur.close()
        self.conn.close()
