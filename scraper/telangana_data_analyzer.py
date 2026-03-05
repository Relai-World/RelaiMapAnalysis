"""
Telangana Property Data - Complete Analysis & Transformation
============================================================
Transforms raw scraped data into clean, analyzable format
"""

import json
import csv
from datetime import datetime
from pathlib import Path
import re

def load_latest_data():
    """Load the most recent scraped data"""
    data_dir = Path(__file__).parent.parent / "scraped_data"
    
    # Find latest market values file
    mv_files = list(data_dir.glob("market_values_*.json"))
    if not mv_files:
        print("No market values data found!")
        return None, None
    
    latest_mv = max(mv_files, key=lambda x: x.stat().st_mtime)
    
    # Find latest hierarchy file
    hier_files = list(data_dir.glob("telangana_hierarchy_*.json"))
    latest_hier = max(hier_files, key=lambda x: x.stat().st_mtime) if hier_files else None
    
    with open(latest_mv, 'r', encoding='utf-8') as f:
        mv_data = json.load(f)
    
    hier_data = None
    if latest_hier:
        with open(latest_hier, 'r', encoding='utf-8') as f:
            hier_data = json.load(f)
    
    return mv_data, hier_data

def transform_market_values(raw_data):
    """Transform raw market value data into clean format"""
    cleaned = []
    
    for record in raw_data.get("market_values", []):
        # The 'effective_from' field contains actual price (e.g., "2,100")
        # The 'unit' field contains the classification/location description
        
        price_str = record.get("effective_from", "0")
        price = float(price_str.replace(",", "").replace("₹", "").strip() or 0)
        
        if price > 0:
            cleaned.append({
                "district": record.get("district"),
                "mandal": record.get("mandal"),
                "village": record.get("village"),
                "classification": record.get("unit", "").strip(),  # Location/road description
                "price_per_sqyd": price,
                "rate_type": record.get("rate_type"),
                "scraped_at": record.get("scraped_at")
            })
    
    return cleaned

def analyze_price_data(cleaned_data):
    """Analyze price data to generate insights"""
    
    # Group by district
    by_district = {}
    for record in cleaned_data:
        dist = record["district"]
        if dist not in by_district:
            by_district[dist] = []
        by_district[dist].append(record)
    
    # Group by village
    by_village = {}
    for record in cleaned_data:
        key = f"{record['district']}|{record['mandal']}|{record['village']}"
        if key not in by_village:
            by_village[key] = []
        by_village[key].append(record)
    
    # Calculate statistics
    stats = {
        "total_records": len(cleaned_data),
        "districts": {},
        "top_locations": [],
        "price_ranges": {}
    }
    
    for dist, records in by_district.items():
        prices = [r["price_per_sqyd"] for r in records if r["price_per_sqyd"] > 0]
        if prices:
            stats["districts"][dist] = {
                "count": len(records),
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "mandals": len(set(r["mandal"] for r in records)),
                "villages": len(set(r["village"] for r in records))
            }
    
    # Find top priced locations
    village_avgs = []
    for key, records in by_village.items():
        prices = [r["price_per_sqyd"] for r in records if r["price_per_sqyd"] > 0]
        if prices:
            parts = key.split("|")
            village_avgs.append({
                "district": parts[0],
                "mandal": parts[1],
                "village": parts[2],
                "avg_price": sum(prices) / len(prices),
                "max_price": max(prices),
                "min_price": min(prices),
                "records": len(records)
            })
    
    # Sort by max price
    village_avgs.sort(key=lambda x: x["max_price"], reverse=True)
    stats["top_locations"] = village_avgs[:20]
    
    # Price range distribution
    ranges = {"0-5000": 0, "5000-10000": 0, "10000-20000": 0, 
              "20000-50000": 0, "50000-100000": 0, "100000+": 0}
    for record in cleaned_data:
        price = record["price_per_sqyd"]
        if price < 5000:
            ranges["0-5000"] += 1
        elif price < 10000:
            ranges["5000-10000"] += 1
        elif price < 20000:
            ranges["10000-20000"] += 1
        elif price < 50000:
            ranges["20000-50000"] += 1
        elif price < 100000:
            ranges["50000-100000"] += 1
        else:
            ranges["100000+"] += 1
    
    stats["price_ranges"] = ranges
    
    return stats

def export_clean_data(cleaned_data, stats):
    """Export cleaned data to files"""
    output_dir = Path(__file__).parent.parent / "scraped_data"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export cleaned CSV
    csv_file = output_dir / f"clean_market_values_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if cleaned_data:
            writer = csv.DictWriter(f, fieldnames=cleaned_data[0].keys())
            writer.writeheader()
            writer.writerows(cleaned_data)
    
    # Export stats JSON
    stats_file = output_dir / f"price_analysis_{timestamp}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # Export top locations CSV
    top_file = output_dir / f"top_locations_{timestamp}.csv"
    with open(top_file, 'w', newline='', encoding='utf-8') as f:
        if stats["top_locations"]:
            writer = csv.DictWriter(f, fieldnames=stats["top_locations"][0].keys())
            writer.writeheader()
            writer.writerows(stats["top_locations"])
    
    return csv_file, stats_file, top_file

def print_analysis(stats):
    """Print analysis summary"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║          TELANGANA PROPERTY MARKET ANALYSIS                       ║
║                                                                   ║
║  Data Source: registration.telangana.gov.in                       ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📊 TOTAL RECORDS ANALYZED: {stats['total_records']}\n")
    
    print("="*70)
    print("📍 DISTRICT-WISE ANALYSIS")
    print("="*70)
    for dist, data in sorted(stats["districts"].items()):
        print(f"\n🏛️ {dist}")
        print(f"   Villages: {data['villages']} | Mandals: {data['mandals']} | Records: {data['count']}")
        print(f"   Price Range: ₹{data['min_price']:,.0f} - ₹{data['max_price']:,.0f} per Sq.Yd")
        print(f"   Average: ₹{data['avg_price']:,.0f} per Sq.Yd")
    
    print("\n" + "="*70)
    print("🏆 TOP 10 HIGHEST PRICED LOCATIONS")
    print("="*70)
    for i, loc in enumerate(stats["top_locations"][:10], 1):
        print(f"\n{i}. {loc['village']} ({loc['mandal']}, {loc['district']})")
        print(f"   Max: ₹{loc['max_price']:,.0f}/Sq.Yd | Avg: ₹{loc['avg_price']:,.0f}/Sq.Yd")
    
    print("\n" + "="*70)
    print("📈 PRICE DISTRIBUTION (Rs per Sq.Yd)")
    print("="*70)
    total = sum(stats["price_ranges"].values())
    for range_name, count in stats["price_ranges"].items():
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"   {range_name:>12}: {bar} {count} ({pct:.1f}%)")

def main():
    print("Loading scraped data...")
    raw_mv, hier_data = load_latest_data()
    
    if not raw_mv:
        print("No data found!")
        return
    
    print(f"Found {len(raw_mv.get('market_values', []))} raw records")
    
    # Transform data
    print("Transforming data...")
    cleaned = transform_market_values(raw_mv)
    print(f"Cleaned {len(cleaned)} records")
    
    # Analyze
    print("Analyzing prices...")
    stats = analyze_price_data(cleaned)
    
    # Export
    print("Exporting results...")
    csv_file, stats_file, top_file = export_clean_data(cleaned, stats)
    
    # Print analysis
    print_analysis(stats)
    
    print("\n" + "="*70)
    print("📁 OUTPUT FILES:")
    print("="*70)
    print(f"  • {csv_file}")
    print(f"  • {stats_file}")
    print(f"  • {top_file}")
    print("="*70)

if __name__ == "__main__":
    main()
