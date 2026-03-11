import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'post@123'),
    dbname=os.getenv('DB_NAME', 'real_estate_intelligence'),
    port=os.getenv('DB_PORT', '5432'),
    sslmode='require' if os.getenv('DB_HOST', 'localhost') != 'localhost' else 'prefer'
)

cur = conn.cursor()
cur.execute("""
    SELECT 
        projectname,
        number_of_towers,
        number_of_floors,
        external_amenities,
        builder_age,
        poc_name,
        project_launch_date,
        possession_date,
        facing
    FROM real_estate_projects 
    WHERE projectname ILIKE '%ACE DEL LAGO%' 
    LIMIT 1
""")

row = cur.fetchone()
if row:
    print(f"Project: {row[0]}")
    print(f"Towers: {row[1]}")
    print(f"Floors: {row[2]}")
    print(f"Amenities: {row[3][:100] if row[3] else 'NULL'}")
    print(f"Builder Age: {row[4]}")
    print(f"POC Name: {row[5]}")
    print(f"Launch Date: {row[6]}")
    print(f"Possession Date: {row[7]}")
    print(f"Facing: {row[8]}")
else:
    print("Property not found")

cur.close()
conn.close()
