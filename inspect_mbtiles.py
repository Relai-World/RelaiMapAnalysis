import sqlite3

conn = sqlite3.connect("tiles/schools.mbtiles")
cur = conn.cursor()

cur.execute("SELECT MIN(zoom_level), MAX(zoom_level) FROM tiles")
print("Zoom range:", cur.fetchone())

cur.execute("SELECT COUNT(*) FROM tiles")
print("Total tiles:", cur.fetchone()[0])

conn.close()
