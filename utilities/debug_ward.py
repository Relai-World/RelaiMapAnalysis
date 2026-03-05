
import requests
import json

# Point for Gachibowli
lat, lon = 17.4436, 78.3519

# Query to find the administrative area (level 8 or 9) containing this point
query = f"""
[out:json][timeout:25];
is_in({lat},{lon})->.a;
relation(pixel.a)["boundary"="administrative"]["admin_level"~"8|9|10"];
out geom;
"""
# Wait, is_in is for areas. Let's try:
query = f"""
[out:json][timeout:25];
relation(around:50,{lat},{lon})["boundary"="administrative"]["admin_level"~"8|9|10"];
out geom;
"""

r = requests.post("https://overpass-api.de/api/interpreter", data=query)
print(r.status_code)
with open("debug_ward.json", "w", encoding="utf-8") as f:
    f.write(r.text)
print("Saved to debug_ward.json")
