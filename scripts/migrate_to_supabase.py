import psycopg2

# --- CONFIG ---
LOCAL_DB = {
    "dbname": "real_estate_intelligence",
    "user": "postgres",
    "password": "post@123",
    "host": "localhost",
    "port": "5432"
}

# Supabase Details (Using Port 6543 for stability)
DB_PASSWORD = "22N81A66@h6"
DB_HOST = "db.ozduxfktrrumtkhmpxrp.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"

def migrate():
    print("🚀 Starting FULL Migration to Supabase...")
    
    try:
        # 1. Connect
        local_conn = psycopg2.connect(**LOCAL_DB)
        local_cur = local_conn.cursor()
        
        sb_conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=6543
        )
        sb_cur = sb_conn.cursor()
        
        # 2. Migrate Locations (Full Columns)
        print("📍 Migrating Locations...")
        local_cur.execute("SELECT name, city, region, ST_AsText(geom), school_count, hospital_count FROM locations")
        locs = local_cur.fetchall()
        for l in locs:
            sb_cur.execute("""
                INSERT INTO locations (name, city, region, geom, school_count, hospital_count) 
                VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    city = EXCLUDED.city,
                    region = EXCLUDED.region,
                    geom = EXCLUDED.geom
            """, l)
        sb_conn.commit()

        # 3. Migrate Insights (Full Columns)
        print("📊 Migrating Insights...")
        local_cur.execute("""
            SELECT l.name, li.avg_sentiment_score, li.growth_score, li.investment_score, 
                   li.sentiment_summary, li.avg_price, li.price_trend, li.schools_count, li.hospitals_count
            FROM location_insights li 
            JOIN locations l ON li.location_id = l.id
        """)
        insights = local_cur.fetchall()
        for i in insights:
            sb_cur.execute("SELECT id FROM locations WHERE name = %s", (i[0],))
            sb_id = sb_cur.fetchone()
            if sb_id:
                data = (sb_id[0],) + i[1:]
                sb_cur.execute("""
                    INSERT INTO location_insights 
                    (location_id, avg_sentiment_score, growth_score, investment_score, 
                     sentiment_summary, avg_price, price_trend, schools_count, hospitals_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (location_id) DO UPDATE SET
                        avg_sentiment_score = EXCLUDED.avg_sentiment_score,
                        growth_score = EXCLUDED.growth_score,
                        investment_score = EXCLUDED.investment_score
                """, data)
        
        sb_conn.commit()
        print("✅ FULL Migration Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'local_conn' in locals(): local_conn.close()
        if 'sb_conn' in locals(): sb_conn.close()

if __name__ == "__main__":
    migrate()
