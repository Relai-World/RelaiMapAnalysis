import pandas as pd
import re
from collections import Counter

# Load the CSV file
csv_file = r"c:\Users\gudde\OneDrive\Desktop\Final\unified_data_DataType_Raghu_rows (1).csv"
df = pd.read_csv(csv_file, low_memory=False)

print("=" * 100)
print("🏢 COMPREHENSIVE AMENITIES ANALYSIS")
print("=" * 100)

# Save output to file
output_file = "amenities_analysis_report.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 100 + "\n")
    f.write("AMENITIES ANALYSIS REPORT\n")
    f.write("=" * 100 + "\n\n")
    
    f.write(f"Dataset: unified_data_DataType_Raghu_rows (1).csv\n")
    f.write(f"Total Rows: {len(df):,}\n")
    f.write(f"Total Columns: {len(df.columns)}\n\n")
    
    f.write("=" * 100 + "\n")
    f.write("ALL COLUMNS IN DATASET\n")
    f.write("=" * 100 + "\n\n")
    
    for i, col in enumerate(df.columns, 1):
        f.write(f"{i:3}. {col}\n")
    
    # Find amenity columns
    f.write("\n" + "=" * 100 + "\n")
    f.write("AMENITY-RELATED COLUMNS\n")
    f.write("=" * 100 + "\n\n")
    
    amenity_keywords = ['amenity', 'amenities', 'facility', 'facilities']
    amenity_cols = [col for col in df.columns if any(kw in col.lower() for kw in amenity_keywords)]
    
    if amenity_cols:
        for col in amenity_cols:
            f.write(f"\n{'='*80}\n")
            f.write(f"Column: {col}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Data Type: {df[col].dtype}\n")
            f.write(f"Non-null values: {df[col].notna().sum():,} / {len(df):,}\n")
            f.write(f"Null values: {df[col].isna().sum():,}\n\n")
            
            # Get unique values
            unique_vals = df[col].dropna().unique()
            f.write(f"Unique values: {len(unique_vals)}\n\n")
            
            # Show sample values
            f.write("Sample values (first 20):\n")
            f.write("-" * 80 + "\n")
            for i, val in enumerate(unique_vals[:20], 1):
                val_str = str(val)[:200]  # Limit to 200 chars
                f.write(f"{i:3}. {val_str}\n")
            
            if len(unique_vals) > 20:
                f.write(f"\n... and {len(unique_vals) - 20} more unique values\n")
            
            # If values contain commas, try to parse individual amenities
            sample_val = str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else ""
            if ',' in sample_val or '|' in sample_val:
                f.write(f"\n{'='*80}\n")
                f.write("PARSING INDIVIDUAL AMENITIES\n")
                f.write(f"{'='*80}\n\n")
                
                all_amenities = []
                for val in df[col].dropna():
                    val_str = str(val)
                    # Split by comma or pipe
                    items = re.split(r'[,|]', val_str)
                    all_amenities.extend([item.strip() for item in items if item.strip()])
                
                # Count frequency
                amenity_counts = Counter(all_amenities)
                
                f.write(f"Total individual amenities found: {len(all_amenities):,}\n")
                f.write(f"Unique amenities: {len(amenity_counts)}\n\n")
                f.write("Top 50 Most Common Amenities:\n")
                f.write("-" * 80 + "\n")
                
                for i, (amenity, count) in enumerate(amenity_counts.most_common(50), 1):
                    percentage = (count / len(df)) * 100
                    f.write(f"{i:3}. {amenity:<50} | Count: {count:>6,} | {percentage:>5.1f}%\n")
    else:
        f.write("No columns with 'amenity' keyword found.\n")
    
    # Check for specific feature columns
    f.write("\n" + "=" * 100 + "\n")
    f.write("OTHER PROPERTY FEATURES\n")
    f.write("=" * 100 + "\n\n")
    
    feature_keywords = ['bhk', 'bedroom', 'bathroom', 'balcony', 'parking', 'floor', 
                       'area', 'sqft', 'price', 'furnish', 'facing', 'age', 'possession']
    
    for keyword in feature_keywords:
        matching = [col for col in df.columns if keyword.lower() in col.lower()]
        if matching:
            f.write(f"\n{keyword.upper()} related columns:\n")
            for col in matching:
                f.write(f"  - {col}\n")

print(f"✅ Analysis complete! Report saved to: {output_file}")
print(f"\nOpening report...")

# Print summary to console
print("\n" + "=" * 100)
print("QUICK SUMMARY")
print("=" * 100)

amenity_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['amenity', 'amenities'])]
if amenity_cols:
    print(f"\n✅ Found {len(amenity_cols)} amenity column(s):")
    for col in amenity_cols:
        print(f"   - {col}")
        
        # Quick sample
        sample = df[col].dropna().head(1)
        if len(sample) > 0:
            print(f"     Sample: {str(sample.iloc[0])[:150]}...")
else:
    print("\n⚠️  No dedicated amenity columns found in the dataset.")

# Show the report
with open(output_file, 'r', encoding='utf-8') as f:
    print("\n" + "=" * 100)
    print("FULL REPORT")
    print("=" * 100)
    print(f.read())
