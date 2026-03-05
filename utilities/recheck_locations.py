import pandas as pd
import numpy as np

# Load the CSV file
csv_file = r"c:\Users\gudde\OneDrive\Desktop\Final\unified_data_DataType_Raghu_rows (1).csv"
df = pd.read_csv(csv_file, low_memory=False)

# Your project locations
project_locations = [
    'Financial District',
    'Gachibowli',
    'HITEC City',
    'Kondapur',
    'Kukatpally',
    'Madhapur',
    'Nanakramguda'
]

print("=" * 100)
print("COMPREHENSIVE LOCATION SEARCH - Checking all possible fields")
print("=" * 100)
print()

# Clean the data
df['baseprojectprice'] = pd.to_numeric(df['baseprojectprice'], errors='coerce')
df['price_per_sft'] = pd.to_numeric(df['price_per_sft'], errors='coerce')

# Filter for Hyderabad only
df_hyderabad = df[df['city'].str.contains('Hyderabad', case=False, na=False)]

print(f"Total records in CSV: {len(df):,}")
print(f"Hyderabad records: {len(df_hyderabad):,}")
print()

# Check what columns might contain location info
location_columns = ['areaname', 'projectlocation', 'google_place_address', 'google_place_name']
print("Checking these columns for location data:")
for col in location_columns:
    if col in df_hyderabad.columns:
        print(f"  ✓ {col}")
print()

results = []

for location in project_locations:
    print(f"🔍 Searching for: {location}")
    print(f"   {'─' * 80}")
    
    # Search in multiple columns with case-insensitive matching
    mask = pd.Series([False] * len(df_hyderabad))
    
    for col in location_columns:
        if col in df_hyderabad.columns:
            col_mask = df_hyderabad[col].astype(str).str.contains(location, case=False, na=False)
            matches = col_mask.sum()
            if matches > 0:
                print(f"   Found {matches} in '{col}'")
            mask = mask | col_mask
    
    location_data = df_hyderabad[mask]
    count = len(location_data)
    
    print(f"   TOTAL MATCHES: {count}")
    
    if count > 0:
        # Calculate averages
        avg_base_price = location_data['baseprojectprice'].mean()
        avg_price_per_sft = location_data['price_per_sft'].mean()
        
        # Get min and max for both base price and price per sqft
        min_base_price = location_data['baseprojectprice'].min()
        max_base_price = location_data['baseprojectprice'].max()
        min_price_sqft = location_data['price_per_sft'].min()
        max_price_sqft = location_data['price_per_sft'].max()
        
        results.append({
            'Location': location,
            'Count': count,
            'Avg Base Price': avg_base_price,
            'Avg Price/SqFt': avg_price_per_sft,
            'Min Base Price': min_base_price,
            'Max Base Price': max_base_price,
            'Min Price/SqFt': min_price_sqft,
            'Max Price/SqFt': max_price_sqft
        })
        
        print(f"   Avg Base Price: ₹{avg_base_price/10000000:.2f} Cr" if not np.isnan(avg_base_price) else "   Avg Base Price: N/A")
        print(f"   Avg Price/SqFt: ₹{avg_price_per_sft:,.0f}" if not np.isnan(avg_price_per_sft) else "   Avg Price/SqFt: N/A")
    
    print()

# Create summary DataFrame
if results:
    print("=" * 100)
    print("DETAILED SUMMARY")
    print("=" * 100)
    summary_df = pd.DataFrame(results)
    
    for _, row in summary_df.iterrows():
        print(f"\n📍 {row['Location'].upper()}")
        print(f"   Properties: {int(row['Count']):,}")
        print(f"   Avg Base Price: ₹{row['Avg Base Price']/10000000:.2f} Cr")
        print(f"   Avg Price/SqFt: ₹{row['Avg Price/SqFt']:,.0f}")
        print(f"   Base Price Range: ₹{row['Min Base Price']/10000000:.2f} Cr - ₹{row['Max Base Price']/10000000:.2f} Cr")
        print(f"   Price/SqFt Range: ₹{row['Min Price/SqFt']:,.0f} - ₹{row['Max Price/SqFt']:,.0f}")
    
    # Save to CSV
    output_file = r"c:\Users\gudde\OneDrive\Desktop\Final\location_avg_costs_detailed.csv"
    summary_df.to_csv(output_file, index=False)
    print()
    print("=" * 100)
    print(f"✅ Detailed summary saved to: location_avg_costs_detailed.csv")
    print(f"📊 Total properties analyzed: {summary_df['Count'].sum():,}")
    print("=" * 100)
else:
    print("⚠️  No matching data found for any location")
