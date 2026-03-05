"""
Create Database Views for Telangana Property Analysis
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_views():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()
    
    print("Creating database views...")
    
    # 1. District Summary View
    cur.execute("""
        CREATE OR REPLACE VIEW v_telangana_district_summary AS
        SELECT 
            d.name as district,
            d.code as district_code,
            d.region,
            COUNT(DISTINCT m.id) as mandal_count,
            COUNT(DISTINCT v.id) as village_count,
            COUNT(mv.id) as price_record_count,
            MIN(mv.price_per_sqyd) as min_price,
            MAX(mv.price_per_sqyd) as max_price,
            AVG(mv.price_per_sqyd) as avg_price
        FROM telangana_districts d
        LEFT JOIN telangana_mandals m ON m.district_code = d.code
        LEFT JOIN telangana_villages v ON v.district_code = d.code
        LEFT JOIN telangana_market_values mv ON mv.district_code = d.code AND mv.price_per_sqyd > 0
        GROUP BY d.name, d.code, d.region
        ORDER BY max_price DESC NULLS LAST;
    """)
    print("  ✓ v_telangana_district_summary")
    
    # 2. Top Locations View
    cur.execute("""
        CREATE OR REPLACE VIEW v_telangana_top_locations AS
        SELECT 
            village,
            mandal,
            district,
            MAX(price_per_sqyd) as max_price,
            MIN(price_per_sqyd) as min_price,
            AVG(price_per_sqyd) as avg_price,
            COUNT(*) as record_count
        FROM telangana_market_values
        WHERE price_per_sqyd > 0
        GROUP BY village, mandal, district
        ORDER BY max_price DESC;
    """)
    print("  ✓ v_telangana_top_locations")
    
    # 3. Price Range Distribution View
    cur.execute("""
        CREATE OR REPLACE VIEW v_telangana_price_distribution AS
        SELECT 
            CASE 
                WHEN price_per_sqyd < 5000 THEN '0-5K'
                WHEN price_per_sqyd < 10000 THEN '5K-10K'
                WHEN price_per_sqyd < 20000 THEN '10K-20K'
                WHEN price_per_sqyd < 50000 THEN '20K-50K'
                WHEN price_per_sqyd < 100000 THEN '50K-100K'
                ELSE '100K+'
            END as price_range,
            COUNT(*) as count,
            district
        FROM telangana_market_values
        WHERE price_per_sqyd > 0
        GROUP BY 1, district
        ORDER BY district, 1;
    """)
    print("  ✓ v_telangana_price_distribution")
    
    # 4. Mandal Summary View
    cur.execute("""
        CREATE OR REPLACE VIEW v_telangana_mandal_summary AS
        SELECT 
            mandal,
            district,
            COUNT(DISTINCT village) as village_count,
            COUNT(*) as price_records,
            MIN(price_per_sqyd) as min_price,
            MAX(price_per_sqyd) as max_price,
            AVG(price_per_sqyd) as avg_price
        FROM telangana_market_values
        WHERE price_per_sqyd > 0
        GROUP BY mandal, district
        ORDER BY max_price DESC;
    """)
    print("  ✓ v_telangana_mandal_summary")
    
    # 5. Area Hierarchy View
    cur.execute("""
        CREATE OR REPLACE VIEW v_telangana_hierarchy AS
        SELECT 
            d.name as district,
            d.region,
            m.name as mandal,
            v.name as village,
            v.code as village_code
        FROM telangana_districts d
        LEFT JOIN telangana_mandals m ON m.district_code = d.code
        LEFT JOIN telangana_villages v ON v.mandal_code = m.code AND v.district_code = d.code
        ORDER BY d.name, m.name, v.name;
    """)
    print("  ✓ v_telangana_hierarchy")
    
    conn.commit()
    
    # Show view counts
    print("\n📊 VIEW STATISTICS:")
    print("-"*50)
    
    views = [
        'v_telangana_district_summary',
        'v_telangana_top_locations',
        'v_telangana_price_distribution',
        'v_telangana_mandal_summary',
        'v_telangana_hierarchy'
    ]
    
    for view in views:
        cur.execute(f"SELECT COUNT(*) FROM {view}")
        count = cur.fetchone()[0]
        print(f"  {view}: {count} rows")
    
    cur.close()
    conn.close()
    print("\n✅ All views created successfully!")

if __name__ == "__main__":
    create_views()
