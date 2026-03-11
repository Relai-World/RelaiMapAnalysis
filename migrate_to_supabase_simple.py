"""
Simplified Database Migration to Supabase
Handles geometry columns and PostGIS extensions properly
"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

def get_local_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def get_supabase_db():
    return psycopg2.connect(
        dbname=os.getenv("SUPABASE_DB_NAME"),
        user=os.getenv("SUPABASE_DB_USER"),
        password=os.getenv("SUPABASE_DB_PASSWORD"),
        host=os.getenv("SUPABASE_DB_HOST"),
        port=os.getenv("SUPABASE_DB_PORT", "5432"),
        sslmode='require'
    )

# Core tables (excluding system/PostGIS tables)
CORE_TABLES = [
    'locations',
    'news_balanced_corpus', 
    'location_insights',
    'location_infrastructure',
    'location_costs',
    'price_trends',
    'real_estate_projects',
    'csv_properties',
    'listings',
    'news_items',
    'processed_sentiment_data',
    'raw_scraped_data',
    'registration_transactions',
    'igrs_property_transactions',
    'igrs_scrape_progress'
]

def setup_supabase_extensions(supabase_conn):
    """Enable required extensions in Supabase"""
    print("🔧 Setting up Supabase extensions...")
    cur = supabase_conn.cursor()
    
    extensions = [
        "CREATE EXTENSION IF NOT EXISTS postgis;",
        "CREATE EXTENSION IF NOT EXISTS postgis_topology;",
        "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;",
        "CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;"
    ]
    
    for ext in extensions:
        try:
            cur.execute(ext)
            supabase_conn.commit()
            print(f"  ✅ {ext}")
        except Exception as e:
            print(f"  ⚠️  {ext} - {e}")
            supabase_conn.rollback()
    
    cur.close()

def export_table_schema(local_conn, table_name):
    """Export table schema using pg_dump approach"""
    print(f"📋 Exporting schema for {table_name}...")
    
    cur = local_conn.cursor()
    
    # Get basic table structure
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default,
               character_maximum_length, numeric_precision, numeric_scale
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    
    # Build CREATE TABLE
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    col_defs = []
    
    for col_name, data_type, nullable, default, max_len, num_prec, num_scale in columns:
        col_def = f"  {col_name} "
        
        # Map data types
        if data_type == 'integer':
            if default and 'nextval' in str(default):
                col_def += "SERIAL"
            else:
                col_def += "INTEGER"
        elif data_type == 'bigint':
            col_def += "BIGINT"
        elif data_type == 'character varying':
            if max_len:
                col_def += f"VARCHAR({max_len})"
            else:
                col_def += "TEXT"
        elif data_type == 'text':
            col_def += "TEXT"
        elif data_type == 'numeric':
            if num_prec and num_scale:
                col_def += f"NUMERIC({num_prec},{num_scale})"
            else:
                col_def += "NUMERIC"
        elif data_type == 'double precision':
            col_def += "DOUBLE PRECISION"
        elif data_type == 'timestamp without time zone':
            col_def += "TIMESTAMP"
        elif data_type == 'date':
            col_def += "DATE"
        elif data_type == 'boolean':
            col_def += "BOOLEAN"
        elif data_type == 'USER-DEFINED':
            # Likely geometry
            col_def += "GEOMETRY"
        else:
            col_def += data_type.upper()
        
        # Nullable
        if nullable == 'NO':
            col_def += " NOT NULL"
        
        # Default (skip serial defaults)
        if default and 'nextval' not in str(default):
            col_def += f" DEFAULT {default}"
        
        col_defs.append(col_def)
    
    create_sql += ",\n".join(col_defs) + "\n);"
    
    cur.close()
    return create_sql

def migrate_table(local_conn, supabase_conn, table_name):
    """Migrate a single table"""
    print(f"\n{'='*50}")
    print(f"MIGRATING: {table_name}")
    print(f"{'='*50}")
    
    try:
        # 1. Create table schema
        schema_sql = export_table_schema(local_conn, table_name)
        
        supabase_cur = supabase_conn.cursor()
        supabase_cur.execute(schema_sql)
        supabase_conn.commit()
        supabase_cur.close()
        print("✅ Table schema created")
        
        # 2. Get row count
        local_cur = local_conn.cursor()
        local_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = local_cur.fetchone()[0]
        print(f"📊 Total rows: {total_rows}")
        
        if total_rows == 0:
            print("⚠️  No data to migrate")
            local_cur.close()
            return 0
        
        # 3. Clear existing data
        supabase_cur = supabase_conn.cursor()
        supabase_cur.execute(f"DELETE FROM {table_name}")
        supabase_conn.commit()
        supabase_cur.close()
        
        # 4. Copy data in batches
        batch_size = 500
        migrated = 0
        
        for offset in range(0, total_rows, batch_size):
            local_cur.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
            batch = local_cur.fetchall()
            
            if not batch:
                break
            
            # Get column names
            columns = [desc[0] for desc in local_cur.description]
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            supabase_cur = supabase_conn.cursor()
            try:
                supabase_cur.executemany(insert_sql, batch)
                supabase_conn.commit()
                migrated += len(batch)
                print(f"  ✅ {migrated}/{total_rows} rows ({migrated/total_rows*100:.1f}%)")
            except Exception as e:
                print(f"  ❌ Batch error: {e}")
                supabase_conn.rollback()
            finally:
                supabase_cur.close()
        
        local_cur.close()
        print(f"✅ Migration complete: {migrated} rows")
        return migrated
        
    except Exception as e:
        print(f"❌ Error migrating {table_name}: {e}")
        return 0

def main():
    print("="*60)
    print("SUPABASE MIGRATION TOOL")
    print("="*60)
    
    # Check credentials
    required_vars = ['SUPABASE_DB_HOST', 'SUPABASE_DB_NAME', 'SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        print("\nPlease add these to your .env file:")
        print("SUPABASE_DB_HOST=db.your-project-ref.supabase.co")
        print("SUPABASE_DB_NAME=postgres")
        print("SUPABASE_DB_USER=postgres")
        print("SUPABASE_DB_PASSWORD=your-password")
        return
    
    try:
        # Connect
        print("🔌 Connecting to databases...")
        local_conn = get_local_db()
        supabase_conn = get_supabase_db()
        print("✅ Connected successfully")
        
        # Setup extensions
        setup_supabase_extensions(supabase_conn)
        
        # Migrate tables
        total_migrated = 0
        successful_tables = 0
        
        for table in CORE_TABLES:
            rows = migrate_table(local_conn, supabase_conn, table)
            total_migrated += rows
            if rows > 0:
                successful_tables += 1
            time.sleep(1)  # Brief pause between tables
        
        print(f"\n{'='*60}")
        print("MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Tables processed: {len(CORE_TABLES)}")
        print(f"✅ Tables with data: {successful_tables}")
        print(f"📊 Total rows migrated: {total_migrated:,}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        try:
            local_conn.close()
            supabase_conn.close()
        except:
            pass

if __name__ == "__main__":
    main()