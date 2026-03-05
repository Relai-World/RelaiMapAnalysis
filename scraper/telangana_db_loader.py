"""
Telangana Property Data - Full Database Loader
==============================================
Creates schema and loads all property data into PostgreSQL

Tables Created:
- telangana_districts: All 33 districts
- telangana_mandals: Mandals per district
- telangana_villages: Villages per mandal
- telangana_market_values: Property prices per sq yard
"""

import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# All 33 Telangana Districts
DISTRICTS = {
    "ADILABAD": "19_1",
    "BHADRADRI KOTHAGUDEM": "22_2",
    "HANUMAKONDA": "21_1",
    "HYDERABAD": "16_1",
    "JAGTIAL": "20_2",
    "JANGOAN": "21_3",
    "JAYASHANKAR BHOOPALPALLY": "21_4",
    "JOGULAMBA GADWAL": "14_2",
    "KAMAREDDY": "18_2",
    "KARIMNAGAR": "20_1",
    "KHAMMAM": "22_1",
    "KOMARAM BHEEM ASIFABAD": "19_4",
    "MAHABUBABAD": "21_5",
    "MAHABUBNAGAR": "14_1",
    "MANCHERIAL": "19_3",
    "MEDAK": "17_1",
    "MEDCHAL-MALKAJGIRI": "15_2",
    "MULUGU": "21_6",
    "NAGARKURNOOL": "14_3",
    "NALGONDA": "23_1",
    "NARAYANPET": "14_5",
    "NIRMAL": "19_2",
    "NIZAMABAD": "18_1",
    "PEDDAPALLI": "20_4",
    "RAJANNA SIRCILLA": "20_3",
    "RANGAREDDY": "15_1",
    "SANGAREDDY": "17_2",
    "SIDDIPET": "17_3",
    "SURYAPET": "23_2",
    "VIKARABAD": "15_3",
    "WANAPARTHY": "14_4",
    "WARANGAL": "21_2",
    "YADADRI BHUVANAGIRI": "23_3",
}


class TelanganaDBLoader:
    """Database loader for Telangana property data"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        logger.info("✅ Connected to database")
    
    def create_schema(self):
        """Create all required tables"""
        logger.info("Creating database schema...")
        
        # Drop existing tables if needed (for fresh start)
        # self.cur.execute("DROP TABLE IF EXISTS telangana_market_values CASCADE")
        # self.cur.execute("DROP TABLE IF EXISTS telangana_villages CASCADE")
        # self.cur.execute("DROP TABLE IF EXISTS telangana_mandals CASCADE")
        # self.cur.execute("DROP TABLE IF EXISTS telangana_districts CASCADE")
        
        # 1. Districts Table
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS telangana_districts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                code VARCHAR(20) NOT NULL UNIQUE,
                region VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Mandals Table
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS telangana_mandals (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) NOT NULL,
                district_id INTEGER REFERENCES telangana_districts(id),
                district_name VARCHAR(100),
                district_code VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, district_code)
            );
        """)
        
        # 3. Villages Table
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS telangana_villages (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                code VARCHAR(20) NOT NULL,
                mandal_id INTEGER REFERENCES telangana_mandals(id),
                mandal_name VARCHAR(100),
                mandal_code VARCHAR(20),
                district_name VARCHAR(100),
                district_code VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, mandal_code, district_code)
            );
        """)
        
        # 4. Market Values Table
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS telangana_market_values (
                id SERIAL PRIMARY KEY,
                district VARCHAR(100) NOT NULL,
                district_code VARCHAR(20),
                mandal VARCHAR(100) NOT NULL,
                mandal_code VARCHAR(20),
                village VARCHAR(150) NOT NULL,
                village_code VARCHAR(20),
                classification VARCHAR(255),
                price_per_sqyd DECIMAL(12, 2) NOT NULL,
                unit VARCHAR(50) DEFAULT 'Sq.Yd',
                rate_type VARCHAR(50) DEFAULT 'Non-Agriculture',
                effective_from VARCHAR(50),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(village_code, classification, rate_type)
            );
        """)
        
        # Create indexes for faster queries
        self.cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_mv_district ON telangana_market_values(district);
            CREATE INDEX IF NOT EXISTS idx_mv_mandal ON telangana_market_values(mandal);
            CREATE INDEX IF NOT EXISTS idx_mv_village ON telangana_market_values(village);
            CREATE INDEX IF NOT EXISTS idx_mv_price ON telangana_market_values(price_per_sqyd);
        """)
        
        self.conn.commit()
        logger.info("✅ Schema created successfully")
    
    def seed_districts(self):
        """Insert all 33 districts"""
        logger.info("Seeding districts...")
        
        for name, code in DISTRICTS.items():
            # Determine region based on code prefix
            prefix = code.split("_")[0]
            if prefix in ["15", "16"]:
                region = "Hyderabad Metro"
            elif prefix in ["17", "18"]:
                region = "North Telangana"
            elif prefix in ["19", "20"]:
                region = "Karimnagar Region"
            elif prefix in ["21"]:
                region = "Warangal Region"
            elif prefix in ["22", "23"]:
                region = "East Telangana"
            elif prefix == "14":
                region = "South Telangana"
            else:
                region = "Telangana"
            
            self.cur.execute("""
                INSERT INTO telangana_districts (name, code, region)
                VALUES (%s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, region = EXCLUDED.region
            """, (name, code, region))
        
        self.conn.commit()
        logger.info(f"✅ Inserted {len(DISTRICTS)} districts")
    
    def insert_mandal(self, mandal_name, mandal_code, district_name, district_code):
        """Insert a mandal"""
        # Get district ID
        self.cur.execute("SELECT id FROM telangana_districts WHERE code = %s", (district_code,))
        result = self.cur.fetchone()
        district_id = result[0] if result else None
        
        self.cur.execute("""
            INSERT INTO telangana_mandals (name, code, district_id, district_name, district_code)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code, district_code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, (mandal_name, mandal_code, district_id, district_name, district_code))
        
        result = self.cur.fetchone()
        return result[0] if result else None
    
    def insert_village(self, village_name, village_code, mandal_name, mandal_code, 
                       district_name, district_code, mandal_id=None):
        """Insert a village"""
        self.cur.execute("""
            INSERT INTO telangana_villages (name, code, mandal_id, mandal_name, mandal_code, 
                                            district_name, district_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (code, mandal_code, district_code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, (village_name, village_code, mandal_id, mandal_name, mandal_code, 
              district_name, district_code))
        
        result = self.cur.fetchone()
        return result[0] if result else None
    
    def insert_market_values(self, values_list):
        """Bulk insert market values"""
        if not values_list:
            return 0
        
        insert_query = """
            INSERT INTO telangana_market_values 
            (district, district_code, mandal, mandal_code, village, village_code,
             classification, price_per_sqyd, unit, rate_type, scraped_at)
            VALUES %s
            ON CONFLICT (village_code, classification, rate_type) 
            DO UPDATE SET price_per_sqyd = EXCLUDED.price_per_sqyd,
                         scraped_at = EXCLUDED.scraped_at
        """
        
        data = [
            (v['district'], v.get('district_code', ''), v['mandal'], v.get('mandal_code', ''),
             v['village'], v.get('village_code', ''), v.get('classification', ''),
             v['price_per_sqyd'], v.get('unit', 'Sq.Yd'), v.get('rate_type', 'Non-Agriculture'),
             datetime.now())
            for v in values_list
        ]
        
        execute_values(self.cur, insert_query, data)
        self.conn.commit()
        return len(data)
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def get_stats(self):
        """Get table statistics"""
        stats = {}
        
        self.cur.execute("SELECT COUNT(*) FROM telangana_districts")
        stats['districts'] = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM telangana_mandals")
        stats['mandals'] = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM telangana_villages")
        stats['villages'] = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM telangana_market_values")
        stats['market_values'] = self.cur.fetchone()[0]
        
        # Price statistics
        self.cur.execute("""
            SELECT 
                MIN(price_per_sqyd) as min_price,
                MAX(price_per_sqyd) as max_price,
                AVG(price_per_sqyd) as avg_price
            FROM telangana_market_values
            WHERE price_per_sqyd > 0
        """)
        price_stats = self.cur.fetchone()
        if price_stats:
            stats['min_price'] = price_stats[0]
            stats['max_price'] = price_stats[1]
            stats['avg_price'] = price_stats[2]
        
        return stats
    
    def close(self):
        """Close connection"""
        self.cur.close()
        self.conn.close()
        logger.info("Database connection closed")


def setup_database():
    """Setup database schema and seed districts"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║       TELANGANA PROPERTY DATABASE SETUP                           ║
║                                                                   ║
║  Creating tables and seeding initial data                         ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    loader = TelanganaDBLoader()
    
    try:
        # Create schema
        loader.create_schema()
        
        # Seed districts
        loader.seed_districts()
        
        # Show stats
        stats = loader.get_stats()
        print("\n" + "="*60)
        print("📊 DATABASE SETUP COMPLETE")
        print("="*60)
        print(f"  Districts:      {stats['districts']}")
        print(f"  Mandals:        {stats['mandals']}")
        print(f"  Villages:       {stats['villages']}")
        print(f"  Market Values:  {stats['market_values']}")
        print("="*60)
        
    finally:
        loader.close()


if __name__ == "__main__":
    setup_database()
