
import json
import os

def convert_topo_to_geo(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data.get('type') != 'Topology':
        print("Not a TopoJSON file")
        return

    scale = data['transform']['scale']
    translate = data['transform']['translate']
    arcs = data['arcs']
    
    def decode_arc(arc):
        coords = []
        x, y = 0, 0
        for dx, dy in arc:
            x += dx
            y += dy
            coords.append([x * scale[0] + translate[0], y * scale[1] + translate[1]])
        return coords

    decoded_arcs = [decode_arc(arc) for arc in arcs]

    def get_geometry(geom):
        if geom['type'] == 'Polygon':
            coords = []
            for ring in geom['arcs']:
                line = []
                for arc_idx in ring:
                    if arc_idx < 0:
                        arc = decoded_arcs[~arc_idx][::-1]
                    else:
                        arc = decoded_arcs[arc_idx]
                    if line:
                        line.extend(arc[1:])
                    else:
                        line.extend(arc)
                coords.append(line)
            return {"type": "Polygon", "coordinates": coords}
        elif geom['type'] == 'MultiPolygon':
            polys = []
            for poly in geom['arcs']:
                rings = []
                for ring in poly:
                    line = []
                    for arc_idx in ring:
                        if arc_idx < 0:
                            arc = decoded_arcs[~arc_idx][::-1]
                        else:
                            arc = decoded_arcs[arc_idx]
                        if line:
                            line.extend(arc[1:])
                        else:
                            line.extend(arc)
                    rings.append(line)
                polys.append(rings)
            return {"type": "MultiPolygon", "coordinates": polys}
        return None

    features = []
    for obj_name, obj in data['objects'].items():
        for geom in obj['geometries']:
            geo = get_geometry(geom)
            if geo:
                features.append({
                    "type": "Feature",
                    "geometry": geo,
                    "properties": geom.get('properties', {})
                })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
    print(f"Converted {input_file} to {output_file}")

if __name__ == "__main__":
    convert_topo_to_geo('telangana.geojson', 'frontend/data/telangana_districts.geojson')
