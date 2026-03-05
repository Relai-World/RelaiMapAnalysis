import pandas as pd
import numpy as np

# Load the CSV file
csv_file = r"c:\Users\gudde\OneDrive\Desktop\Final\unified_data_DataType_Raghu_rows (1).csv"
df = pd.read_csv(csv_file, low_memory=False)

print("=" * 80)
print("🏢 ANALYZING AMENITIES IN DATASET")
print("=" * 80)

print(f"\n📊 Dataset Overview:")
print(f"   Total Rows: {len(df):,}")
print(f"   Total Columns: {len(df.columns)}")

# Get all column names
print(f"\n📋 All Column Names ({len(df.columns)} columns):")
print("-" * 80)
for i, col in enumerate(df.columns, 1):
    print(f"{i:3}. {col}")

# Look for amenity-related columns
print("\n" + "=" * 80)
print("🎯 AMENITY-RELATED COLUMNS")
print("=" * 80)

amenity_keywords = ['amenity', 'amenities', 'facility', 'facilities', 'feature', 'features']
amenity_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in amenity_keywords)]

if amenity_columns:
    print(f"\nFound {len(amenity_columns)} amenity-related columns:")
    for col in amenity_columns:
        print(f"\n📍 Column: {col}")
        print(f"   Data Type: {df[col].dtype}")
        print(f"   Non-null Count: {df[col].notna().sum():,} / {len(df):,}")
        
        # Show sample values
        sample_values = df[col].dropna().unique()[:10]
        if len(sample_values) > 0:
            print(f"   Sample Values:")
            for val in sample_values:
                print(f"      - {val}")
else:
    print("\n⚠️  No columns with 'amenity' keyword found.")
    print("   Searching for other potential amenity columns...")

# Check for specific amenity types
specific_amenities = [
    'school', 'hospital', 'mall', 'park', 'gym', 'pool', 'swimming',
    'club', 'playground', 'garden', 'security', 'parking', 'lift',
    'power', 'water', 'gas', 'internet', 'wifi', 'cctv', 'sports'
]

print("\n" + "=" * 80)
print("🔍 SEARCHING FOR SPECIFIC AMENITY TYPES")
print("=" * 80)

found_amenity_cols = {}
for amenity in specific_amenities:
    matching_cols = [col for col in df.columns if amenity.lower() in col.lower()]
    if matching_cols:
        found_amenity_cols[amenity] = matching_cols

if found_amenity_cols:
    for amenity, cols in found_amenity_cols.items():
        print(f"\n🏷️  {amenity.upper()}:")
        for col in cols:
            print(f"   - {col}")
else:
    print("\n⚠️  No specific amenity columns found.")

# Try to find any column that might contain amenity data
print("\n" + "=" * 80)
print("📝 ANALYZING POTENTIAL AMENITY COLUMNS")
print("=" * 80)

# Look for columns with list-like or comma-separated values
for col in df.columns:
    sample = df[col].dropna().head(5)
    if len(sample) > 0:
        # Check if values contain commas (might be amenity lists)
        has_commas = sample.astype(str).str.contains(',').any()
        if has_commas and df[col].dtype == 'object':
            print(f"\n📌 {col} (might contain amenity lists):")
            print(f"   Sample values:")
            for val in sample.head(3):
                val_str = str(val)[:100]  # Limit length
                print(f"      {val_str}")

print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
