import sqlite3, json

conn = sqlite3.connect("tiles/schools.mbtiles")
cur = conn.cursor()
cur.execute("SELECT value FROM metadata WHERE name='json'")
meta = json.loads(cur.fetchone()[0])

print(meta["vector_layers"])
conn.close()
