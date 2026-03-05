import pandas as pd
import re
from collections import Counter

# Load just a sample to see structure
df = pd.read_csv(r'unified_data_DataType_Raghu_rows (1).csv', nrows=100, low_memory=False)

print("=" * 100)
print("AMENITIES COLUMNS FOUND")
print("=" * 100)

# Find amenity columns
amenity_cols = [c for c in df.columns if 'amenity' in c.lower() or 'amenities' in c.lower()]

print(f"\nFound {len(amenity_cols)} amenity-related columns:\n")
for col in amenity_cols:
    print(f"  ✓ {col}")

# Now load full dataset for these columns only
print("\n" + "=" * 100)
print("LOADING FULL DATASET FOR AMENITY COLUMNS...")
print("=" * 100)

df_full = pd.read_csv(r'unified_data_DataType_Raghu_rows (1).csv', 
                      usecols=amenity_cols, 
                      low_memory=False)

print(f"\nTotal rows: {len(df_full):,}\n")

# Analyze each amenity column
for col in amenity_cols:
    print("\n" + "=" * 100)
    print(f"COLUMN: {col}")
    print("=" * 100)
    
    print(f"Non-null values: {df_full[col].notna().sum():,} / {len(df_full):,}")
    print(f"Null values: {df_full[col].isna().sum():,}")
    
    # Show sample values
    print("\nSample values (first 10 non-null):")
    print("-" * 100)
    samples = df_full[col].dropna().head(10)
    for i, val in enumerate(samples, 1):
        val_str = str(val)[:150]
        print(f"{i:2}. {val_str}")
    
    # Try to extract individual amenities
    print("\n" + "-" * 100)
    print("EXTRACTING INDIVIDUAL AMENITIES...")
    print("-" * 100)
    
    all_amenities = []
    for val in df_full[col].dropna():
        val_str = str(val)
        # Try different separators
        if ',' in val_str:
            items = val_str.split(',')
        elif '|' in val_str:
            items = val_str.split('|')
        elif ';' in val_str:
            items = val_str.split(';')
        else:
            items = [val_str]
        
        all_amenities.extend([item.strip() for item in items if item.strip()])
    
    # Count frequency
    amenity_counts = Counter(all_amenities)
    
    print(f"\nTotal amenity entries: {len(all_amenities):,}")
    print(f"Unique amenities: {len(amenity_counts):,}")
    
    print(f"\nTop 30 Most Common Amenities:")
    print("-" * 100)
    print(f"{'Rank':<6} {'Amenity':<60} {'Count':<10} {'%'}")
    print("-" * 100)
    
    for i, (amenity, count) in enumerate(amenity_counts.most_common(30), 1):
        percentage = (count / len(df_full)) * 100
        print(f"{i:<6} {amenity:<60} {count:<10,} {percentage:>5.1f}%")

print("\n" + "=" * 100)
print("✅ ANALYSIS COMPLETE")
print("=" * 100)
