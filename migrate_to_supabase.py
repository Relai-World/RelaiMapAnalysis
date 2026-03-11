"""
Complete Database Migration to Supabase
Migrates all 18 tables from local PostgreSQL to Supabase
"""

import psycopg2
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import time

load_dotenv()

# Local PostgreSQL connection
def get_local_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

# Supabase connection (you'll need to add these to .env)
def get_supabase_db():
    return psycopg2.connect(
        dbname=os.getenv("SUPABASE_DB_NAME"),
        user=os.getenv("SUPABASE_DB_USER"),
        password=os.getenv("SUPABASE_DB_PASSWORD"),
        host=os.getenv("SUPABASE_DB_HOST"),
        port=os.getenv("SUPABASE_DB_PORT", "5432"),
        sslmode='require'
    )

# Tables to migrate (excluding system tables)
TABLES_TO_MIGRATE = [
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

def get_table_schema(local_conn, table_name):
    """Get CREATE TABLE statement for a table"""
    cur = local_conn.cursor()
    
    # Get column definitions
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, 
               is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table_name,))
    
    columns = cur.fetchall()
    
    # Get constraints
    cur.execute("""
        SELECT constraint_name, constraint_type, column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = %s
    """, (table_name,))
    
    constraints = cur.fetchall()
    
    # Build CREATE TABLE statement
    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
    
    column_defs = []
    for col_name, data_type, max_length, nullable, default in columns:
        col_def = f"  {col_name} "
        
        # Handle data types
        if data_type == 'character varying':
            if max_length:
                col_def += f"VARCHAR({max_length})"
            else:
                col_def += "TEXT"
        elif data_type == 'timestamp without time zone':
            col_def += "TIMESTAMP"
        elif data_type == 'USER-DEFINED':  # Likely geometry
            col_def += "GEOMETRY"
        else:
            col_def += data_type.upper()
        
        # Handle nullable
        if nullable == 'NO':
            col_def += " NOT NULL"
        
        # Handle default
        if default:
            if 'nextval' in default:
                col_def += " SERIAL"
            else:
                col_def += f" DEFAULT {default}"
        
        column_defs.append(col_def)
    
    create_sql += ",\n".join(column_defs)
    
    # Add primary key
    for constraint_name, constraint_type, column_name in constraints:
        if constraint_type == 'PRIMARY KEY':
            create_sql += f",\n  PRIMARY KEY ({column_name})"
            break
    
    create_sql += "\n);"
    
    cur.close()
    return create_sql

def migrate_table_data(local_conn, supabase_conn, table_name, batch_size=1000):
    """Migrate data from local to Supabase in batches"""
    print(f"\n📊 Migrating data for {table_name}...")
    
    local_cur = local_conn.cursor()
    supabase_cur = supabase_conn.cursor()
    
    # Get total count
    local_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = local_cur.fetchone()[0]
    print(f"  Total rows: {total_rows}")
    
    if total_rows == 0:
        print(f"  ⚠️  No data to migrate for {table_name}")
        return 0
    
    # Get column names
    local_cur.execute(f"SELECT * FROM {table_name} LIMIT 1")
    columns = [desc[0] for desc in local_cur.description]
    
    # Clear existing data in Supabase
    try:
        supabase_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        supabase_conn.commit()
        print(f"  🗑️  Cleared existing data")
    except Exception as e:
        print(f"  ⚠️  Could not clear table: {e}")
        supabase_conn.rollback()
    
    # Migrate in batches
    migrated = 0
    offset = 0
    
    while offset < total_rows:
        # Fetch batch from local
        local_cur.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
        batch = local_cur.fetchall()
        
        if not batch:
            break
        
        # Prepare insert statement
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        
        try:
            # Insert batch to Supabase
            supabase_cur.executemany(insert_sql, batch)
            supabase_conn.commit()
            
            migrated += len(batch)
            print(f"  ✅ Migrated {migrated}/{total_rows} rows ({migrated/total_rows*100:.1f}%)")
            
        except Exception as e:
            print(f"  ❌ Error migrating batch at offset {offset}: {e}")
            supabase_conn.rollback()
            
            # Try individual inserts for this batch
            for row in batch:
                try:
                    supabase_cur.execute(insert_sql, row)
                    supabase_conn.commit()
                    migrated += 1
                except Exception as row_error:
                    print(f"    ⚠️  Skipped row: {row_error}")
                    supabase_conn.rollback()
        
        offset += batch_size
        time.sleep(0.1)  # Small delay to avoid overwhelming the connection
    
    local_cur.close()
    supabase_cur.close()
    
    print(f"  ✅ Completed: {migrated}/{total_rows} rows migrated")
    return migrated

def create_table_in_supabase(supabase_conn, table_name, create_sql):
    """Create table in Supabase"""
    print(f"\n🏗️  Creating table: {table_name}")
    
    cur = supabase_conn.cursor()
    try:
        cur.execute(create_sql)
        supabase_conn.commit()
        print(f"  ✅ Table {table_name} created successfully")
        return True
    except Exception as e:
        print(f"  ❌ Error creating table {table_name}: {e}")
        supabase_conn.rollback()
        return False
    finally:
        cur.close()

def main():
    print("="*80)
    print("DATABASE MIGRATION TO SUPABASE")
    print("="*80)
    print(f"Tables to migrate: {len(TABLES_TO_MIGRATE)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment variables
    required_vars = [
        'SUPABASE_DB_NAME', 'SUPABASE_DB_USER', 
        'SUPABASE_DB_PASSWORD', 'SUPABASE_DB_HOST'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        print("Please add these to your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return
    
    try:
        # Connect to databases
        print("\n🔌 Connecting to databases...")
        local_conn = get_local_db()
        supabase_conn = get_supabase_db()
        print("  ✅ Connected to both databases")
        
        migration_stats = {
            'tables_created': 0,
            'tables_migrated': 0,
            'total_rows': 0,
            'failed_tables': []
        }
        
        # Migrate each table
        for table_name in TABLES_TO_MIGRATE:
            try:
                print(f"\n{'='*60}")
                print(f"MIGRATING: {table_name.upper()}")
                print(f"{'='*60}")
                
                # Get schema and create table
                create_sql = get_table_schema(local_conn, table_name)
                print(f"📋 Schema extracted")
                
                if create_table_in_supabase(supabase_conn, table_name, create_sql):
                    migration_stats['tables_created'] += 1
                    
                    # Migrate data
                    rows_migrated = migrate_table_data(local_conn, supabase_conn, table_name)
                    migration_stats['total_rows'] += rows_migrated
                    
                    if rows_migrated > 0:
                        migration_stats['tables_migrated'] += 1
                else:
                    migration_stats['failed_tables'].append(table_name)
                
            except Exception as e:
                print(f"❌ Failed to migrate {table_name}: {e}")
                migration_stats['failed_tables'].append(table_name)
        
        # Final summary
        print("\n" + "="*80)
        print("MIGRATION COMPLETE")
        print("="*80)
        print(f"✅ Tables created: {migration_stats['tables_created']}/{len(TABLES_TO_MIGRATE)}")
        print(f"✅ Tables with data migrated: {migration_stats['tables_migrated']}")
        print(f"📊 Total rows migrated: {migration_stats['total_rows']:,}")
        
        if migration_stats['failed_tables']:
            print(f"❌ Failed tables: {migration_stats['failed_tables']}")
        
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    
    finally:
        try:
            local_conn.close()
            supabase_conn.close()
            print("\n🔌 Database connections closed")
        except:
            pass

if __name__ == "__main__":
    main()