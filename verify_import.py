import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
c = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)
cur = c.cursor()
cur.execute('SELECT COUNT(*) FROM real_estate_projects;')
print('Row count:', cur.fetchone()[0])
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='real_estate_projects' LIMIT 5;")
for r in cur.fetchall():
    print(r)
c.close()
