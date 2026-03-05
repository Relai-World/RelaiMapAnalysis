
import psycopg2
conn = psycopg2.connect('dbname=real_estate_intelligence user=postgres password=post@123')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'news_balanced_corpus'")
for r in cur.fetchall():
    print(r)
conn.close()
