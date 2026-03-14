"""
Export location_costs table to CSV
====================================
Exports all data from location_costs table to a CSV file
"""
import psycopg2
import os
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_NAME = os.getenv("DB_NAME", "real_estate_intelligence")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "post@123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def export_location_costs():
    """Export location_costs table to CSV"""
    
    # Connect to database
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    cur = conn.cursor()
    
    # Fetch all data from location_costs
    print("Fetching data from location_costs table...")
    cur.execute("""
        SELECT 
            id,
            location_id,
            location_name,
            property_count,
            avg_base_price,
            avg_price_sqft,
            min_base_price,
            max_base_price,
            min_price_sqft,
            max_price_sqft,
            created_at
        FROM location_costs
        ORDER BY location_name
    """)
    
    rows = cur.fetchall()
    
    # Get column names
    col_names = [desc[0] for desc in cur.description]
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"location_costs_export_{timestamp}.csv"
    
    # Write to CSV
    print(f"Exporting {len(rows)} records to {filename}...")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(col_names)
        
        # Write data
        writer.writerows(rows)
    
    print(f"\n✅ Export completed successfully!")
    print(f"📄 File saved: {os.path.abspath(filename)}")
    print(f"📊 Total records: {len(rows)}")
    
    # Print summary statistics
    if rows:
        print("\n📈 SUMMARY STATISTICS:")
        print(f"   Locations exported: {len(rows)}")
        
        # Calculate averages
        avg_prop_count = sum(row[3] for row in rows if row[3]) / len([row for row in rows if row[3]])
        avg_price_sqft = sum(row[5] for row in rows if row[5]) / len([row for row in rows if row[5]])
        
        print(f"   Avg properties per location: {avg_prop_count:.1f}")
        print(f"   Avg price/sqft: ₹{avg_price_sqft:.2f}")
    
    cur.close()
    conn.close()
    
    return filename

if __name__ == "__main__":
    try:
        export_location_costs()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
