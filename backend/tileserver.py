import sqlite3
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Vector Tile Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MBTILES_PATH = "tiles/schools.mbtiles"

@app.get("/tiles/schools/{z}/{x}/{y}.pbf")
def schools_tiles(z: int, x: int, y: int):
    # TMS y flip (mandatory)
    tms_y = (1 << z) - 1 - y

    conn = sqlite3.connect(MBTILES_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT tile_data
        FROM tiles
        WHERE zoom_level = ?
          AND tile_column = ?
          AND tile_row = ?
    """, (z, x, tms_y))

    row = cur.fetchone()
    conn.close()

    if not row:
        return Response(status_code=204)

    return Response(
        content=row[0],
        media_type="application/x-protobuf",
        headers={"Content-Encoding": "gzip"}
    )
