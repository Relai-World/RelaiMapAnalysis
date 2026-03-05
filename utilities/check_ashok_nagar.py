
import psycopg2
import sys
sys.stdout.reconfigure(encoding='utf-8')
conn=psycopg2.connect('dbname=real_estate_intelligence user=postgres password=post@123')
cur=conn.cursor()
cur.execute("""
    SELECT content, url FROM news_balanced_corpus 
    WHERE location_name = 'Ashok Nagar' 
    ORDER BY id DESC 
    LIMIT 5
""")
print("--- Ashok Nagar Samples ---")
for r in cur.fetchall():
    print(r[0][:100].replace('\n', ' '))
    print(r[1])
    print("-" * 20)
conn.close()
