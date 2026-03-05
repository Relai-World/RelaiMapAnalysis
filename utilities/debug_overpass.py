
import requests
import json

query = """
[out:json][timeout:60];
area["name"="Hyderabad"]->.a;
(
  relation["place"~"suburb|neighbourhood"](area.a);
  way["place"~"suburb|neighbourhood"](area.a);
);
out geom;
"""

r = requests.post("https://overpass-api.de/api/interpreter", data=query)
print(r.status_code)
with open("debug_overpass.json", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Saved to debug_overpass.json")
