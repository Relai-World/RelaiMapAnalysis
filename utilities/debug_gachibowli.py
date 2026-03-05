
import requests
import json

query = """
[out:json][timeout:25];
(
  node["name"="Gachibowli"];
  way["name"="Gachibowli"];
  relation["name"="Gachibowli"];
);
out geom;
"""

r = requests.post("https://overpass-api.de/api/interpreter", data=query)
print(r.status_code)
with open("debug_gachibowli.json", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Saved to debug_gachibowli.json")
