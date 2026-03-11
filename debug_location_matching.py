"""
Debug location name matching between locations and properties_final tables
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def debug_matching():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        
        print("="*60)
        print("LOCATION NAMES IN LOCATIONS TABLE")
        print("="*60)
        
        # Get location names from locations table
        cur.execute("SELECT id, name FROM locations WHERE name ILIKE '%hitech%' OR name ILIKE '%hitec%' ORDER BY name")
        locations = cur.fetchall()
        print("HITEC/HITECH related locations:")
        for loc_id, name in locations:
            print(f"  ID {loc_id}: '{name}'")
        
        print("\n" + "="*60)
        print("AREA NAMES IN PROPERTIES_FINAL TABLE")
        print("="*60)
        
        # Get area names from properties_final table
        cur.execute("""
            SELECT DISTINCT areaname, COUNT(*) as count 
            FROM properties_final 
            WHERE areaname ILIKE '%hitech%' OR areaname ILIKE '%hitec%'
            GROUP BY areaname 
            ORDER BY areaname
        """)
        areas = cur.fetchall()
        print("HITEC/HITECH related areas in properties_final:")
        for area, count in areas:
            print(f"  '{area}': {count} properties")
        
        print("\n" + "="*60)
        print("TESTING EXACT MATCHING")
        print("="*60)
        
        # Test exact matching for HITEC City
        test_names = ['HITEC City', 'Hi Tech City', 'Hitech City', 'HITECH City']
        
        for test_name in test_names:
            cur.execute("""
                SELECT COUNT(*) 
                FROM properties_final 
                WHERE LOWER(areaname) = LOWER(%s)
                    AND price_per_sft IS NOT NULL 
                    AND price_per_sft != 'None' 
                    AND price_per_sft != ''
            """, (test_name,))
            count = cur.fetchone()[0]
            print(f"  '{test_name}' matches: {count} properties")
        
        print("\n" + "="*60)
        print("ALL UNIQUE AREA NAMES (SAMPLE)")
        print("="*60)
        
        # Get sample of all area names
        cur.execute("""
            SELECT DISTINCT areaname, COUNT(*) as count 
            FROM properties_final 
            WHERE city = 'Hyderabad'
            GROUP BY areaname 
            ORDER BY count DESC 
            LIMIT 20
        """)
        all_areas = cur.fetchall()
        print("Top 20 Hyderabad areas by property count:")
        for area, count in all_areas:
            print(f"  '{area}': {count} properties")
        
        print("\n" + "="*60)
        print("LOCATION VS PROPERTIES MATCHING TEST")
        print("="*60)
        
        # Test matching between tables
        cur.execute("""
            SELECT 
                l.name as location_name,
                pf.areaname,
                COUNT(*) as match_count
            FROM locations l
            LEFT JOIN properties_final pf ON LOWER(l.name) = LOWER(pf.areaname)
            WHERE l.name ILIKE '%hitec%' OR l.name ILIKE '%hitech%'
            GROUP BY l.name, pf.areaname
            ORDER BY l.name
        """)
        matches = cur.fetchall()
        print("Location to Properties matching:")
        for loc_name, area_name, count in matches:
            print(f"  Location: '{loc_name}' -> Area: '{area_name}' ({count} matches)")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_matching()