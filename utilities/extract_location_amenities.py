import pandas as pd
import re
from collections import Counter

# Your 7 project locations
TARGET_LOCATIONS = [
    'Financial District',
    'Gachibowli',
    'HITEC City',
    'Kondapur',
    'Kukatpally',
    'Madhapur',
    'Nanakramguda'
]

print("=" * 100)
print("🎯 EXTRACTING AMENITIES FOR YOUR 7 LOCATIONS")
print("=" * 100)

# Load the CSV
print("\n📂 Loading CSV file...")
df = pd.read_csv(r'unified_data_DataType_Raghu_rows (1).csv', low_memory=False)
print(f"✓ Loaded {len(df):,} rows")

# Find amenity columns
amenity_cols = [c for c in df.columns if 'amenity' in c.lower() or 'amenities' in c.lower()]
print(f"\n✓ Found {len(amenity_cols)} amenity columns: {amenity_cols}")

# Find location column
location_cols = [c for c in df.columns if 'location' in c.lower() or 'area' in c.lower()]
print(f"✓ Found {len(location_cols)} location-related columns")

# Try to identify the correct location column
print("\n🔍 Identifying location column...")
for col in location_cols[:5]:  # Check first 5
    print(f"\n  Checking: {col}")
    sample = df[col].dropna().head(3)
    for val in sample:
        print(f"    Sample: {str(val)[:80]}")

# Use the most likely location columns
location_column = None
for col in ['areaname', 'projectlocation', 'location', 'area']:
    if col in df.columns:
        location_column = col
        break

if not location_column:
    location_column = location_cols[0] if location_cols else None

print(f"\n✓ Using location column: {location_column}")

# Filter data for your 7 locations
print("\n" + "=" * 100)
print("📍 FILTERING DATA FOR YOUR LOCATIONS")
print("=" * 100)

location_data = {}

for target_loc in TARGET_LOCATIONS:
    # Try to match location (case-insensitive, partial match)
    mask = df[location_column].str.contains(target_loc, case=False, na=False) if location_column else pd.Series([False] * len(df))
    
    # Also try other location columns
    if 'projectlocation' in df.columns and location_column != 'projectlocation':
        mask |= df['projectlocation'].str.contains(target_loc, case=False, na=False)
    if 'areaname' in df.columns and location_column != 'areaname':
        mask |= df['areaname'].str.contains(target_loc, case=False, na=False)
    
    filtered = df[mask]
    location_data[target_loc] = filtered
    print(f"\n{target_loc:<25} → {len(filtered):>6,} properties found")

# Extract amenities for each location
print("\n" + "=" * 100)
print("🏢 EXTRACTING AMENITIES BY LOCATION")
print("=" * 100)

results = {}

for location, data in location_data.items():
    print(f"\n{'='*100}")
    print(f"📍 {location.upper()}")
    print(f"{'='*100}")
    print(f"Properties: {len(data):,}")
    
    if len(data) == 0:
        print("⚠️  No data found for this location")
        results[location] = []
        continue
    
    all_amenities = []
    
    # Extract from all amenity columns
    for col in amenity_cols:
        for val in data[col].dropna():
            val_str = str(val)
            # Split by common separators
            if ',' in val_str:
                items = val_str.split(',')
            elif '|' in val_str:
                items = val_str.split('|')
            elif ';' in val_str:
                items = val_str.split(';')
            else:
                items = [val_str]
            
            all_amenities.extend([item.strip() for item in items if item.strip() and item.strip().lower() != 'nan'])
    
    # Count and display
    amenity_counts = Counter(all_amenities)
    
    print(f"\nTotal amenity mentions: {len(all_amenities):,}")
    print(f"Unique amenities: {len(amenity_counts):,}")
    
    print(f"\n{'Rank':<6} {'Amenity':<50} {'Count':<10} {'% of Properties'}")
    print("-" * 100)
    
    top_amenities = []
    for i, (amenity, count) in enumerate(amenity_counts.most_common(50), 1):
        percentage = (count / len(data)) * 100
        print(f"{i:<6} {amenity:<50} {count:<10,} {percentage:>5.1f}%")
        top_amenities.append({
            'amenity': amenity,
            'count': count,
            'percentage': percentage
        })
    
    results[location] = top_amenities

# Save to file
print("\n" + "=" * 100)
print("💾 SAVING RESULTS")
print("=" * 100)

output_file = "AMENITIES_BY_LOCATION.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 100 + "\n")
    f.write("AMENITIES ANALYSIS - 7 WEST HYDERABAD LOCATIONS\n")
    f.write("=" * 100 + "\n\n")
    
    for location, amenities in results.items():
        f.write(f"\n{'='*100}\n")
        f.write(f"{location.upper()}\n")
        f.write(f"{'='*100}\n")
        f.write(f"Properties analyzed: {len(location_data[location]):,}\n")
        f.write(f"Unique amenities: {len(amenities)}\n\n")
        
        if amenities:
            f.write(f"{'Rank':<6} {'Amenity':<50} {'Count':<10} {'%'}\n")
            f.write("-" * 100 + "\n")
            for i, item in enumerate(amenities, 1):
                f.write(f"{i:<6} {item['amenity']:<50} {item['count']:<10,} {item['percentage']:>5.1f}%\n")
        else:
            f.write("No amenities data found.\n")
        
        f.write("\n")

print(f"✅ Results saved to: {output_file}")

# Create summary
print("\n" + "=" * 100)
print("📊 SUMMARY")
print("=" * 100)

for location in TARGET_LOCATIONS:
    data_count = len(location_data[location])
    amenity_count = len(results[location])
    print(f"{location:<25} → {data_count:>6,} properties | {amenity_count:>3} unique amenities")

print("\n✅ ANALYSIS COMPLETE!")
