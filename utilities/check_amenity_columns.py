import pandas as pd

df = pd.read_csv(r'unified_data_DataType_Raghu_rows (1).csv', nrows=5)

amenity_cols = [c for c in df.columns if 'amenity' in c.lower() or 'amenities' in c.lower()]

print("Amenity columns found:", amenity_cols)
print("\n" + "="*80)

for col in amenity_cols:
    print(f"\nColumn: {col}")
    print(f"Data type: {df[col].dtype}")
    print("\nSample values:")
    for i, val in enumerate(df[col].head(5)):
        print(f"  Row {i+1}: {val}")
