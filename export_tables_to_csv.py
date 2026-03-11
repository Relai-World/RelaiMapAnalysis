"""
Export All Database Tables to CSV Files
Creates a 'database_tables' folder and exports each table as CSV
"""

import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

def get_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def get_all_tables(conn):
    """Get list of all user tables (excluding system tables)"""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name NOT IN ('geography_columns', 'geometry_columns', 'spatial_ref_sys')
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    return tables

def get_table_info(conn, table_name):
    """Get table information (row count, columns)"""
    cur = conn.cursor()
    
    # Get row count
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cur.fetchone()[0]
    
    # Get column info
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    
    cur.close()
    return row_count, columns

def export_table_to_csv(conn, table_name, output_dir):
    """Export a single table to CSV"""
    print(f"\n📊 Exporting: {table_name}")
    
    try:
        # Get table info
        row_count, columns = get_table_info(conn, table_name)
        print(f"  Rows: {row_count:,}")
        print(f"  Columns: {len(columns)}")
        
        if row_count == 0:
            print(f"  ⚠️  Table is empty, creating empty CSV")
            # Create empty CSV with headers
            column_names = [col[0] for col in columns]
            empty_df = pd.DataFrame(columns=column_names)
            csv_path = os.path.join(output_dir, f"{table_name}.csv")
            empty_df.to_csv(csv_path, index=False)
            return True, 0
        
        # Export data using pandas (handles large datasets well)
        query = f"SELECT * FROM {table_name}"
        
        # Handle geometry columns by converting to text
        cur = conn.cursor()
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' 
            AND data_type = 'USER-DEFINED'
        """)
        geometry_columns = [row[0] for row in cur.fetchall()]
        cur.close()
        
        if geometry_columns:
            # Convert geometry columns to WKT text
            select_parts = []
            for col_name, col_type in columns:
                if col_name in geometry_columns:
                    select_parts.append(f"ST_AsText({col_name}) as {col_name}")
                else:
                    select_parts.append(col_name)
            query = f"SELECT {', '.join(select_parts)} FROM {table_name}"
        
        # Read data in chunks for large tables
        chunk_size = 10000
        csv_path = os.path.join(output_dir, f"{table_name}.csv")
        
        if row_count > chunk_size:
            print(f"  📦 Large table, exporting in chunks...")
            first_chunk = True
            
            for offset in range(0, row_count, chunk_size):
                chunk_query = f"{query} LIMIT {chunk_size} OFFSET {offset}"
                df_chunk = pd.read_sql_query(chunk_query, conn)
                
                # Write chunk to CSV
                df_chunk.to_csv(
                    csv_path, 
                    mode='w' if first_chunk else 'a',
                    header=first_chunk,
                    index=False
                )
                first_chunk = False
                
                progress = min(offset + chunk_size, row_count)
                print(f"    Progress: {progress:,}/{row_count:,} ({progress/row_count*100:.1f}%)")
        else:
            # Small table, export all at once
            df = pd.read_sql_query(query, conn)
            df.to_csv(csv_path, index=False)
        
        print(f"  ✅ Exported to: {csv_path}")
        return True, row_count
        
    except Exception as e:
        print(f"  ❌ Error exporting {table_name}: {e}")
        return False, 0

def create_export_summary(output_dir, export_results):
    """Create a summary file of the export"""
    summary = {
        "export_date": datetime.now().isoformat(),
        "total_tables": len(export_results),
        "successful_exports": sum(1 for success, _ in export_results.values() if success),
        "total_rows_exported": sum(rows for success, rows in export_results.values() if success),
        "tables": {}
    }
    
    for table_name, (success, row_count) in export_results.items():
        summary["tables"][table_name] = {
            "success": success,
            "row_count": row_count,
            "csv_file": f"{table_name}.csv" if success else None
        }
    
    # Save summary as JSON
    summary_path = os.path.join(output_dir, "export_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save summary as readable text
    summary_text_path = os.path.join(output_dir, "export_summary.txt")
    with open(summary_text_path, 'w') as f:
        f.write("DATABASE EXPORT SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Export Date: {summary['export_date']}\n")
        f.write(f"Total Tables: {summary['total_tables']}\n")
        f.write(f"Successful Exports: {summary['successful_exports']}\n")
        f.write(f"Total Rows Exported: {summary['total_rows_exported']:,}\n\n")
        
        f.write("TABLE DETAILS:\n")
        f.write("-" * 50 + "\n")
        for table_name, info in summary["tables"].items():
            status = "✅" if info["success"] else "❌"
            f.write(f"{status} {table_name}: {info['row_count']:,} rows\n")
    
    return summary_path, summary_text_path

def main():
    print("=" * 70)
    print("DATABASE TABLES CSV EXPORT")
    print("=" * 70)
    
    # Create output directory
    output_dir = "database_tables"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Created directory: {output_dir}")
    else:
        print(f"📁 Using existing directory: {output_dir}")
    
    try:
        # Connect to database
        print("\n🔌 Connecting to database...")
        conn = get_db()
        print("✅ Connected successfully")
        
        # Get all tables
        tables = get_all_tables(conn)
        print(f"\n📋 Found {len(tables)} tables to export:")
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")
        
        # Export each table
        print(f"\n🚀 Starting export...")
        export_results = {}
        
        for i, table_name in enumerate(tables, 1):
            print(f"\n[{i}/{len(tables)}] " + "=" * 50)
            success, row_count = export_table_to_csv(conn, table_name, output_dir)
            export_results[table_name] = (success, row_count)
        
        # Create summary
        print(f"\n📄 Creating export summary...")
        summary_json, summary_txt = create_export_summary(output_dir, export_results)
        
        # Final summary
        successful = sum(1 for success, _ in export_results.values() if success)
        total_rows = sum(rows for success, rows in export_results.values() if success)
        
        print(f"\n" + "=" * 70)
        print("EXPORT COMPLETE")
        print("=" * 70)
        print(f"✅ Successfully exported: {successful}/{len(tables)} tables")
        print(f"📊 Total rows exported: {total_rows:,}")
        print(f"📁 Files saved to: {os.path.abspath(output_dir)}")
        print(f"📄 Summary files:")
        print(f"   - {summary_json}")
        print(f"   - {summary_txt}")
        
        # List all CSV files created
        csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        print(f"\n📋 CSV files created ({len(csv_files)}):")
        for csv_file in sorted(csv_files):
            file_path = os.path.join(output_dir, csv_file)
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            print(f"   - {csv_file} ({size_mb:.1f} MB)")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
    
    finally:
        try:
            conn.close()
            print("\n🔌 Database connection closed")
        except:
            pass

if __name__ == "__main__":
    main()