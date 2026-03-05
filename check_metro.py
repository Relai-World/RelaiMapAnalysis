import json
from pmtiles.reader import Reader

with open("frontend/maptiles/metro.pmtiles", "rb") as f:
    def getter(offset, length):
        f.seek(offset)
        return f.read(length)
    reader = Reader(getter)
    metadata = reader.metadata()
    with open("metro_metadata.json", "w") as out:
        json.dump(metadata, out, indent=2)
