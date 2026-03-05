"""Test OSM query for Gachibowli"""
import requests
import json

# Multiple query strategies
queries = [
    # Strategy 1: Search by name in Hyderabad area
    """
    [out:json][timeout:60];
    area["name"="Hyderabad"]["admin_level"="6"]->.searchArea;
    (
      relation["place"~"suburb|neighbourhood"]["name"~"Gachibowli",i](area.searchArea);
      way["place"~"suburb|neighbourhood"]["name"~"Gachibowli",i](area.searchArea);
      relation["boundary"]["name"~"Gachibowli",i](area.searchArea);
    );
    out geom;
    """,
    
    # Strategy 2: Search around known coordinates
    """
    [out:json][timeout:60];
    (
      relation["place"](around:3000,17.4436,78.3520);
      way["place"~"suburb|neighbourhood"](around:3000,17.4436,78.3520);
    );
    out geom;
    """,
    
    # Strategy 3: Search for any boundary/area with Gachibowli
    """
    [out:json][timeout:60];
    (
      relation["name"~"Gachibowli",i]["boundary"];
      way["name"~"Gachibowli",i]["landuse"];
      relation["name"~"Gachibowli",i];
    );
    out geom;
    """
]

headers = {'User-Agent': 'HydPropertyIntel/1.0'}

for i, query in enumerate(queries, 1):
    print(f"\n{'='*60}")
    print(f"Strategy {i}")
    print('='*60)
    
    try:
        r = requests.post(
            'https://overpass-api.de/api/interpreter',
            data={'data': query},
            headers=headers,
            timeout=60
        )
        
        if r.status_code != 200:
            print(f"Error: HTTP {r.status_code}")
            continue
        
        data = r.json()
        elements = data.get('elements', [])
        
        print(f"Found {len(elements)} elements")
        
        for el in elements[:5]:
            tags = el.get('tags', {})
            name = tags.get('name', 'Unnamed')
            place = tags.get('place', tags.get('boundary', tags.get('landuse', '?')))
            el_type = el.get('type')
            el_id = el.get('id')
            
            print(f"  - {name} ({place}) [{el_type}/{el_id}]")
            
            # Check if it has geometry
            if el.get('geometry') or el.get('members'):
                print(f"    Has geometry: Yes")
            elif el.get('bounds'):
                print(f"    Has bounds: {el.get('bounds')}")
            else:
                print(f"    Has geometry: No")
                
    except Exception as e:
        print(f"Error: {e}")
