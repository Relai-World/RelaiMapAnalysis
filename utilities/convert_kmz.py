import zipfile
import json
import os
import xml.etree.ElementTree as ET

def kmz_to_kml(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as kmz:
        kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
        if not kml_files:
            raise ValueError("No KML file found in KMZ archive.")
        kml_content = kmz.read(kml_files[0])
    return kml_content

def parse_kml_coordinates(coords_str):
    coords = []
    for line in coords_str.strip().split():
        parts = line.split(',')
        if len(parts) >= 2:
            coords.append([float(parts[0]), float(parts[1])])
    return coords

def kml_to_geojson(kml_content, output_path):
    root = ET.fromstring(kml_content)
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    features = []
    
    # Correct namespace handling (some KMLs don't use namespaces correctly or use default)
    # Trying without namespace first if findall returns empty, then with.
    placemarks = root.findall('.//Placemark')
    if not placemarks:
        placemarks = root.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

    for pm in placemarks:
        properties = {}
        geometry = None
        
        # Name & Description
        name = pm.find('name')
        if name is not None: properties['name'] = name.text
        
        desc = pm.find('description')
        if desc is not None: properties['description'] = desc.text

        # Geometry (Support Point, LineString, Polygon)
        # Check for LineString
        line = pm.find('.//LineString')
        if not line: line = pm.find('.//{http://www.opengis.net/kml/2.2}LineString')
        
        point = pm.find('.//Point')
        if not point: point = pm.find('.//{http://www.opengis.net/kml/2.2}Point')

        polygon = pm.find('.//Polygon')
        if not polygon: polygon = pm.find('.//{http://www.opengis.net/kml/2.2}Polygon')
        
        if line is not None:
            coords_tag = line.find('coordinates')
            if not coords_tag: coords_tag = line.find('{http://www.opengis.net/kml/2.2}coordinates')
            if coords_tag is not None:
                geometry = {
                    "type": "LineString",
                    "coordinates": parse_kml_coordinates(coords_tag.text)
                }
        elif point is not None:
            coords_tag = point.find('coordinates')
            if not coords_tag: coords_tag = point.find('{http://www.opengis.net/kml/2.2}coordinates')
            if coords_tag is not None:
                c = parse_kml_coordinates(coords_tag.text)
                if c:
                    geometry = {
                        "type": "Point",
                        "coordinates": c[0]
                    }
        elif polygon is not None:
            # Simplified polygon support (outer boundary only)
            outer = polygon.find('.//outerBoundaryIs//coordinates')
            if not outer: outer = polygon.find('.//{http://www.opengis.net/kml/2.2}outerBoundaryIs//{http://www.opengis.net/kml/2.2}coordinates')
            
            if outer is not None:
                geometry = {
                    "type": "Polygon",
                    "coordinates": [parse_kml_coordinates(outer.text)]
                }

        if geometry:
            features.append({
                "type": "Feature",
                "properties": properties,
                "geometry": geometry
            })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"DTO: Converted {len(features)} features to GeoJSON at {output_path}")

if __name__ == "__main__":
    kmz_path = "RRR_Folder_RRR.kmz"
    geojson_path = "frontend/maptiles/rrr.geojson"
    
    try:
        if not os.path.exists("frontend"): os.makedirs("frontend/maptiles")
        
        print(f"Extracting {kmz_path}...")
        kml_content = kmz_to_kml(kmz_path)
        
        print(f"Converting to GeoJSON...")
        kml_to_geojson(kml_content, geojson_path)
        
    except Exception as e:
        print(f"Error: {e}")
