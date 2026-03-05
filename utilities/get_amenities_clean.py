import pandas as pd
import json
from collections import Counter

# Your 7 locations
LOCATIONS = ['Financial District', 'Gachibowli', 'HITEC City', 'Kondapur', 'Kukatpally', 'Madhapur', 'Nanakramguda']

print("Loading data...")
df = pd.read_csv(r'unified_data_DataType_Raghu_rows (1).csv', low_memory=False)

# Find amenity columns
amenity_cols = [c for c in df.columns if 'amenity' in c.lower() or 'amenities' in c.lower()]
print(f"Amenity columns: {amenity_cols}\n")

results = {}

for location in LOCATIONS:
    # Filter for this location
    mask = (df['areaname'].str.contains(location, case=False, na=False) | 
            df['projectlocation'].str.contains(location, case=False, na=False))
    
    loc_data = df[mask]
    
    # Collect all amenities
    all_amenities = []
    for col in amenity_cols:
        for val in loc_data[col].dropna():
            items = str(val).replace('|', ',').replace(';', ',').split(',')
            all_amenities.extend([item.strip() for item in items if item.strip() and item.strip().lower() != 'nan'])
    
    # Count
    counts = Counter(all_amenities)
    
    results[location] = {
        'property_count': len(loc_data),
        'total_amenity_mentions': len(all_amenities),
        'unique_amenities': len(counts),
        'top_amenities': dict(counts.most_common(30))
    }
    
    print(f"{location}: {len(loc_data)} properties, {len(counts)} unique amenities")

# Save as JSON
with open('amenities_data.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n✅ Saved to amenities_data.json")

# Print summary
print("\n" + "="*80)
print("AMENITIES SUMMARY")
print("="*80)

for loc, data in results.items():
    print(f"\n{loc}:")
    print(f"  Properties: {data['property_count']}")
    print(f"  Unique amenities: {data['unique_amenities']}")
    print(f"  Top 10:")
    for i, (amenity, count) in enumerate(list(data['top_amenities'].items())[:10], 1):
        pct = (count / data['property_count'] * 100) if data['property_count'] > 0 else 0
        print(f"    {i:2}. {amenity:<40} {count:>4} ({pct:>5.1f}%)")
