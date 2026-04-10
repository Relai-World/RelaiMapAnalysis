#!/usr/bin/env python3
"""
Convert KML to GeoJSON
Requires: pip install lxml
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

def kml_to_geojson(kml_file, output_file):
    """Convert KML to GeoJSON format"""
    
    # Parse KML
    tree = ET.parse(kml_file)
    root = tree.getroot()
    
    # KML namespace
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    # Initialize GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Extract Placemarks
    for placemark in root.findall('.//kml:Placemark', ns):
        feature = {
            "type": "Feature",
            "properties": {},
            "geometry": None
        }
        
        # Extract name
        name = placemark.find('kml:name', ns)
        if name is not None and name.text:
            feature["properties"]["name"] = name.text
        
        # Extract description
        description = placemark.find('kml:description', ns)
        if description is not None and description.text:
            feature["properties"]["description"] = description.text
        
        # Extract extended data
        extended_data = placemark.find('kml:ExtendedData', ns)
        if extended_data is not None:
            for data in extended_data.findall('kml:Data', ns):
                name_attr = data.get('name')
                value = data.find('kml:value', ns)
                if name_attr and value is not None and value.text:
                    feature["properties"][name_attr] = value.text
        
        # Extract Point geometry
        point = placemark.find('.//kml:Point/kml:coordinates', ns)
        if point is not None and point.text:
            coords = point.text.strip().split(',')
            if len(coords) >= 2:
                feature["geometry"] = {
                    "type": "Point",
                    "coordinates": [float(coords[0]), float(coords[1])]
                }
        
        # Extract LineString geometry
        linestring = placemark.find('.//kml:LineString/kml:coordinates', ns)
        if linestring is not None and linestring.text:
            coords_text = linestring.text.strip().split()
            coordinates = []
            for coord in coords_text:
                parts = coord.split(',')
                if len(parts) >= 2:
                    coordinates.append([float(parts[0]), float(parts[1])])
            if coordinates:
                feature["geometry"] = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
        
        # Extract Polygon geometry
        polygon = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
        if polygon is not None and polygon.text:
            coords_text = polygon.text.strip().split()
            coordinates = []
            for coord in coords_text:
                parts = coord.split(',')
                if len(parts) >= 2:
                    coordinates.append([float(parts[0]), float(parts[1])])
            if coordinates:
                feature["geometry"] = {
                    "type": "Polygon",
                    "coordinates": [coordinates]
                }
        
        # Add feature if it has geometry
        if feature["geometry"]:
            geojson["features"].append(feature)
    
    # Write GeoJSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(geojson['features'])} features")
    print(f"📄 Output: {output_file}")
    
    # Print file size
    size = Path(output_file).stat().st_size
    print(f"📊 File size: {size:,} bytes ({size/1024:.1f} KB)")

if __name__ == "__main__":
    input_kml = "frontend/data/e56d21e8-0c44-4c35-9e5d-c732f6f59c97.kml"
    output_geojson = "frontend/data/converted_from_kml.geojson"
    
    print("🔄 Converting KML to GeoJSON...")
    kml_to_geojson(input_kml, output_geojson)
    print("✅ Conversion complete!")
