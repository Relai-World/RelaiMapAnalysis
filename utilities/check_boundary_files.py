"""Check existing boundary files"""
import json

# Check hyd_boundaries.geojson
print("="*60)
print("📁 hyd_boundaries.geojson")
print("="*60)

with open('frontend/data/hyd_boundaries.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data.get('features', [])
print(f"Total features: {len(features)}")
print("\nSample properties:")
for feat in features[:15]:
    props = feat.get('properties', {})
    name = props.get('Name') or props.get('name') or props.get('NAME') or props.get('WARD_NAME') or props.get('locality') or str(props)[:50]
    geom_type = feat.get('geometry', {}).get('type', 'Unknown')
    print(f"  • {name} ({geom_type})")

# Check hyderabad_boundaries.geojson
print("\n" + "="*60)
print("📁 hyderabad_boundaries.geojson")
print("="*60)

with open('frontend/data/hyderabad_boundaries.geojson', 'r', encoding='utf-8') as f:
    data2 = json.load(f)

features2 = data2.get('features', [])
print(f"Total features: {len(features2)}")
print("\nSample properties:")
for feat in features2[:15]:
    props = feat.get('properties', {})
    name = props.get('Name') or props.get('name') or props.get('NAME') or props.get('WARD_NAME') or props.get('locality') or str(props)[:50]
    geom_type = feat.get('geometry', {}).get('type', 'Unknown')
    print(f"  • {name} ({geom_type})")

# Print all property keys from first feature
print("\n" + "="*60)
print("📋 Property keys in hyd_boundaries:")
print("="*60)
if features:
    print(list(features[0].get('properties', {}).keys()))

print("\n📋 Property keys in hyderabad_boundaries:")
if features2:
    print(list(features2[0].get('properties', {}).keys()))
