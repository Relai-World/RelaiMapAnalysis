import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(host='localhost', user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'), dbname=os.getenv('DB_NAME'),
    port='5432', sslmode='prefer')
cur = conn.cursor()
cur.execute("""
    SELECT tc.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_name = 'locations'
    ORDER BY tc.table_name;
""")
print("Tables referencing locations:")
for r in cur.fetchall():
    print(f"  table={r[0]}, column={r[1]}")
cur.close()
conn.close()
