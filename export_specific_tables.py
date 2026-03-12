import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def export_tables():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    
    tables_to_export = ["price_trends", "locations", "location_infrastructure"]
    output_dir = r"c:\Users\gudde\OneDrive\Desktop\Final"

    for table_name in tables_to_export:
        print(f"Exporting {table_name}...")
        
        cur = conn.cursor()
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
        columns = cur.fetchall()
        
        select_parts = []
        for col_name, data_type in columns:
            if data_type == 'USER-DEFINED': # Handle PostGIS geometry
                select_parts.append(f"ST_AsText({col_name}) as {col_name}")
            else:
                select_parts.append(col_name)
                
        query = f"SELECT {', '.join(select_parts)} FROM {table_name}"
        
        df = pd.read_sql_query(query, conn)
        csv_path = os.path.join(output_dir, f"{table_name}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path} ({len(df)} rows)")
        
        cur.close()

    conn.close()

if __name__ == "__main__":
    export_tables()
