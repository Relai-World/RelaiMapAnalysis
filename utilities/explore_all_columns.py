import pandas as pd

# Load a sample
df = pd.read_csv(r'unified_data_DataType_Raghu_rows (1).csv', nrows=1000)

print("="*100)
print("ALL COLUMNS IN DATASET")
print("="*100)
print(f"\nTotal columns: {len(df.columns)}\n")

for i, col in enumerate(df.columns, 1):
    non_null = df[col].notna().sum()
    pct = (non_null / len(df)) * 100
    print(f"{i:3}. {col:<50} | Non-null: {non_null:>4}/{len(df)} ({pct:>5.1f}%)")

# Look for columns that might contain amenity-like data
print("\n" + "="*100)
print("POTENTIAL AMENITY/FEATURE COLUMNS")
print("="*100)

keywords = ['feature', 'facility', 'spec', 'detail', 'description', 'highlight']
potential_cols = []

for col in df.columns:
    if any(kw in col.lower() for kw in keywords):
        potential_cols.append(col)

if potential_cols:
    print(f"\nFound {len(potential_cols)} potential columns:\n")
    for col in potential_cols:
        print(f"  - {col}")
        # Show sample
        sample = df[col].dropna().head(2)
        if len(sample) > 0:
            for val in sample:
                val_str = str(val)[:150]
                print(f"      Sample: {val_str}")
else:
    print("\nNo obvious amenity columns found.")
    print("\nLet me check columns with high data density...")
    
    # Find columns with lots of data
    dense_cols = []
    for col in df.columns:
        if df[col].dtype == 'object':  # Text columns
            non_null_pct = (df[col].notna().sum() / len(df)) * 100
            if non_null_pct > 50:  # More than 50% filled
                dense_cols.append((col, non_null_pct))
    
    print(f"\nText columns with >50% data:")
    for col, pct in sorted(dense_cols, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {col:<40} ({pct:.1f}% filled)")
