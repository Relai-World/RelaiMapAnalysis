import psycopg2

class BaseScraper:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="real_estate_intelligence",
            user="postgres",
            password="post@123",
            host="localhost",
            port=5432
        )
        self.cur = self.conn.cursor()

    # ---------- LOCATION ----------
    def get_location_id(self, location_name):
        self.cur.execute(
            "SELECT id FROM locations WHERE LOWER(name) = LOWER(%s)",
            (location_name,)
        )
        row = self.cur.fetchone()
        return row[0] if row else None

    # ---------- DUPLICATE CHECK ----------
    def is_duplicate(self, content):
        self.cur.execute(
            "SELECT 1 FROM raw_scraped_data WHERE content = %s LIMIT 1",
            (content,)
        )
        return self.cur.fetchone() is not None

    # ---------- INSERT ----------
    def insert_raw_data(self, location_id, source, url, content, price=None):
        self.cur.execute("""
            INSERT INTO raw_scraped_data
            (location_id, source, source_url, content, price)
            VALUES (%s, %s, %s, %s, %s)
        """, (location_id, source, url, content, price))
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()
