import pandas as pd

# Read the results
df = pd.read_csv(r"c:\Users\gudde\OneDrive\Desktop\Final\location_avg_costs.csv")

print("=" * 100)
print("AVERAGE COST PER LOCATION - West Hyderabad Intelligence Project")
print("=" * 100)
print()

for _, row in df.iterrows():
    location = row['Location']
    count = int(row['Count'])
    avg_base = row['Avg Base Price']
    avg_sqft = row['Avg Price/SqFt']
    min_price = row['Min Price']
    max_price = row['Max Price']
    
    print(f"📍 {location.upper()}")
    print(f"   {'─' * 80}")
    print(f"   Properties Found:       {count:,}")
    print(f"   Average Base Price:     ₹{avg_base:,.2f} ({avg_base/10000000:.2f} Cr)")
    print(f"   Average Price/SqFt:     ₹{avg_sqft:,.2f}")
    print(f"   Price Range:            ₹{min_price:,.0f} - ₹{max_price:,.0f}")
    print(f"                           ({min_price/10000000:.2f} Cr - {max_price/10000000:.2f} Cr)")
    print()

print("=" * 100)
print("QUICK COMPARISON")
print("=" * 100)
print()

# Sort by average price per sqft
df_sorted = df.sort_values('Avg Price/SqFt', ascending=False)

print("🏆 RANKING BY PRICE PER SQFT:")
print()
for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
    print(f"   {i}. {row['Location']:20s} - ₹{row['Avg Price/SqFt']:,.2f}/sqft")

print()
print("💰 RANKING BY AVERAGE BASE PRICE:")
print()
df_sorted_base = df.sort_values('Avg Base Price', ascending=False)
for i, (_, row) in enumerate(df_sorted_base.iterrows(), 1):
    print(f"   {i}. {row['Location']:20s} - ₹{row['Avg Base Price']/10000000:.2f} Cr")

print()
print("=" * 100)
print(f"📊 OVERALL STATISTICS:")
print(f"   Total Properties Analyzed: {df['Count'].sum():,}")
print(f"   Overall Avg Price/SqFt:    ₹{df['Avg Price/SqFt'].mean():,.2f}")
print(f"   Overall Avg Base Price:    ₹{df['Avg Base Price'].mean()/10000000:.2f} Cr")
print("=" * 100)
