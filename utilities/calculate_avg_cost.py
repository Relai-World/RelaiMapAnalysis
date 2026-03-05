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

print("=" * 80)
print("AVERAGE COST PER LOCATION - West Hyderabad Intelligence Project")
print("=" * 80)
print()

# Clean the data
df['baseprojectprice'] = pd.to_numeric(df['baseprojectprice'], errors='coerce')
df['price_per_sft'] = pd.to_numeric(df['price_per_sft'], errors='coerce')

# Filter for Hyderabad only
df_hyderabad = df[df['city'].str.contains('Hyderabad', case=False, na=False)]

print(f"Total records in CSV: {len(df):,}")
print(f"Hyderabad records: {len(df_hyderabad):,}")
print()

results = []

for location in project_locations:
    # Try to match location in different columns
    location_data = df_hyderabad[
        df_hyderabad['areaname'].str.contains(location, case=False, na=False) |
        df_hyderabad['projectlocation'].str.contains(location, case=False, na=False)
    ]
    
    if len(location_data) > 0:
        # Calculate averages
        avg_base_price = location_data['baseprojectprice'].mean()
        avg_price_per_sft = location_data['price_per_sft'].mean()
        count = len(location_data)
        
        # Get min and max
        min_price = location_data['baseprojectprice'].min()
        max_price = location_data['baseprojectprice'].max()
        
        results.append({
            'Location': location,
            'Count': count,
            'Avg Base Price': avg_base_price,
            'Avg Price/SqFt': avg_price_per_sft,
            'Min Price': min_price,
            'Max Price': max_price
        })
        
        print(f"📍 {location}")
        print(f"   Properties Found: {count}")
        print(f"   Average Base Price: ₹{avg_base_price:,.2f}" if not np.isnan(avg_base_price) else "   Average Base Price: N/A")
        print(f"   Average Price/SqFt: ₹{avg_price_per_sft:,.2f}" if not np.isnan(avg_price_per_sft) else "   Average Price/SqFt: N/A")
        print(f"   Price Range: ₹{min_price:,.0f} - ₹{max_price:,.0f}" if not np.isnan(min_price) else "   Price Range: N/A")
        print()
    else:
        print(f"📍 {location}")
        print(f"   ⚠️  No data found in CSV")
        print()

# Create summary DataFrame
if results:
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    summary_df = pd.DataFrame(results)
    print(summary_df.to_string(index=False))
    
    # Save to CSV
    output_file = r"c:\Users\gudde\OneDrive\Desktop\Final\location_avg_costs.csv"
    summary_df.to_csv(output_file, index=False)
    print()
    print(f"✅ Summary saved to: {output_file}")
else:
    print("⚠️  No matching data found for any location")

print()
print("=" * 80)
