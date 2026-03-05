import requests
import json

base_url = "https://tgrac.telangana.gov.in/arcgis/rest/services/TGRAC/RRR/MapServer"

def check_layer(layer_id=0):
    url = f"{base_url}/{layer_id}?f=json"
    try:
        r = requests.get(url, verify=False, timeout=10) # Verify=False often needed for gov sites
        if r.status_code == 200:
            data = r.json()
            print(f"Layer {layer_id}: {data.get('name')} ({data.get('type')})")
            return data
        else:
            print(f"Failed to access layer {layer_id}: {r.status_code}")
    except Exception as e:
        print(f"Error accessing {url}: {e}")
    return None

def download_geojson(layer_id=0):
    query_url = f"{base_url}/{layer_id}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson",
        "returnGeometry": "true"
    }
    
    print(f"Attempting to download features from Layer {layer_id}...")
    try:
        r = requests.get(query_url, params=params, verify=False, timeout=30)
        if r.status_code == 200:
            try:
                data = r.json()
                if "features" in data and len(data["features"]) > 0:
                    print(f"Success! Found {len(data['features'])} features.")
                    with open("rrr.geojson", "w") as f:
                        json.dump(data, f)
                    print("Saved to rrr.geojson")
                    return True
                else:
                    print("No features returned (or empty). Response keys:", data.keys())
            except json.JSONDecodeError:
                print("Response was not JSON.")
        else:
            print(f"Query failed: {r.status_code}")
    except Exception as e:
        print(f"Error querying: {e}")
    return False

if __name__ == "__main__":
    # Check Layer 0 first
    meta = check_layer(0)
    if meta and meta.get('type') == "Feature Layer":
        download_geojson(0)
    elif meta and meta.get('type') == "Group Layer":
        # Maybe check sublayers?
        print("Layer 0 is a group layer.")
    else:
        # Try finding layers
        print("Checking service info...")
        r = requests.get(f"{base_url}?f=json", verify=False)
        if r.status_code == 200:
            print(r.json().get('layers'))
