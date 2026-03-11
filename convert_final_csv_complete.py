"""
Convert complete final.csv to PostgreSQL table
"""

import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "post@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

def create_simple_table():
    """Create a simple table with all TEXT columns"""
    
    create_table_sql = """
    DROP TABLE IF EXISTS properties_final;
    CREATE TABLE properties_final (
        id SERIAL PRIMARY KEY,
        rera_number TEXT,
        projectname TEXT,
        buildername TEXT,
        baseprojectprice TEXT,
        projectbrochure TEXT,
        projectlocation TEXT,
        project_type TEXT,
        communitytype TEXT,
        total_land_area TEXT,
        number_of_towers TEXT,
        number_of_floors TEXT,
        number_of_flats_per_floor TEXT,
        total_number_of_units TEXT,
        project_launch_date TEXT,
        possession_date TEXT,
        construction_status TEXT,
        open_space TEXT,
        carpet_area_percentage TEXT,
        floor_to_ceiling_height TEXT,
        price_per_sft TEXT,
        external_amenities TEXT,
        specification TEXT,
        powerbackup TEXT,
        no_of_passenger_lift TEXT,
        no_of_service_lift TEXT,
        visitor_parking TEXT,
        ground_vehicle_movement TEXT,
        bhk TEXT,
        facing TEXT,
        sqfeet TEXT,
        sqyard TEXT,
        no_of_car_parkings TEXT,
        amount_for_extra_car_parking TEXT,
        home_loan TEXT,
        complaint_details TEXT,
        construction_material TEXT,
        commission_percentage TEXT,
        after_agreement_of_sale_what_is_payout_time_period TEXT,
        is_lead_registration_required_before_site_visit TEXT,
        turnaround_time_for_lead_acknowledgement TEXT,
        is_there_validity_period_for_registered_lead TEXT,
        accepted_modes_of_lead_registration TEXT,
        status TEXT,
        useremail TEXT,
        poc_name TEXT,
        poc_contact TEXT,
        poc_role TEXT,
        createdat TEXT,
        updatedat TEXT,
        verified TEXT,
        areaname TEXT,
        pricesheet_link TEXT,
        pricesheet_link_1 TEXT,
        total_buildup_area TEXT,
        uds TEXT,
        fsi TEXT,
        main_door_height TEXT,
        available_banks_for_loan TEXT,
        floor_rise_charges TEXT,
        floor_rise_amount_per_floor TEXT,
        floor_rise_applicable_above_floor_no TEXT,
        facing_charges TEXT,
        preferential_location_charges TEXT,
        preferential_location_charges_conditions TEXT,
        project_status TEXT,
        google_place_id TEXT,
        google_place_name TEXT,
        google_place_address TEXT,
        google_place_location TEXT,
        google_place_rating TEXT,
        google_place_user_ratings_total TEXT,
        google_maps_location TEXT,
        google_place_raw_data TEXT,
        hospitals_count TEXT,
        shopping_malls_count TEXT,
        schools_count TEXT,
        restaurants_count TEXT,
        restaurants_above_4_stars_count TEXT,
        supermarkets_count TEXT,
        it_offices_count TEXT,
        metro_stations_count TEXT,
        railway_stations_count TEXT,
        nearest_hospitals TEXT,
        nearest_shopping_malls TEXT,
        nearest_schools TEXT,
        nearest_restaurants TEXT,
        high_rated_restaurants TEXT,
        nearest_supermarkets TEXT,
        nearest_it_offices TEXT,
        nearest_metro_station TEXT,
        nearest_railway_station TEXT,
        nearest_orr_access TEXT,
        connectivity_score TEXT,
        amenities_score TEXT,
        amenities_raw_data TEXT,
        amenities_updated_at TEXT,
        mobile_google_map_url TEXT,
        grid_score TEXT,
        isavailable TEXT,
        configsoldoutstatus TEXT,
        city TEXT,
        state TEXT,
        cp TEXT,
        builder_age TEXT,
        builder_completed_properties TEXT,
        builder_ongoing_projects TEXT,
        builder_operating_locations TEXT,
        builder_origin_city TEXT,
        builder_total_properties TEXT,
        builder_upcoming_properties TEXT,
        alternative_contact TEXT,
        tier TEXT,
        project_update_status TEXT,
        source_of_information TEXT,
        is_landlord_share TEXT,
        landlord_poc_name TEXT,
        landlord_poc_contact TEXT,
        price_per_sft_update_date TEXT,
        configuration_update_date TEXT,
        landlord_investor_update_date TEXT,
        images TEXT
    );
    """
    
    return create_table_sql

def clean_data_simple(df):
    """Convert everything to string and handle nulls"""
    df_clean = df.copy()
    
    # Convert all columns to string and handle nulls
    for col in df_clean.columns:
        df_clean[col] = df_clean[col].astype(str)
        df_clean[col] = df_clean[col].replace(['nan', 'NaN', 'None', 'null', '<NA>'], None)
        df_clean[col] = df_clean[col].replace('', None)
    
    # Handle special column names
    if 'GRID_Score' in df_clean.columns:
        df_clean['grid_score'] = df_clean['GRID_Score']
        df_clean = df_clean.drop('GRID_Score', axis=1)
    
    if 'Landlord/Investor_Update_Date' in df_clean.columns:
        df_clean['landlord_investor_update_date'] = df_clean['Landlord/Investor_Update_Date']
        df_clean = df_clean.drop('Landlord/Investor_Update_Date', axis=1)
    
    return df_clean

def insert_data_simple(conn, df_clean, batch_size=100):
    """Simple insertion with string data"""
    cur = conn.cursor()
    
    total_rows = len(df_clean)
    
    # Get column names that exist in both dataframe and our expected schema
    expected_columns = [
        'rera_number', 'projectname', 'buildername', 'baseprojectprice', 'projectbrochure',
        'projectlocation', 'project_type', 'communitytype', 'total_land_area', 'number_of_towers',
        'number_of_floors', 'number_of_flats_per_floor', 'total_number_of_units', 'project_launch_date',
        'possession_date', 'construction_status', 'open_space', 'carpet_area_percentage',
        'floor_to_ceiling_height', 'price_per_sft', 'external_amenities', 'specification',
        'powerbackup', 'no_of_passenger_lift', 'no_of_service_lift', 'visitor_parking',
        'ground_vehicle_movement', 'bhk', 'facing', 'sqfeet', 'sqyard', 'no_of_car_parkings',
        'amount_for_extra_car_parking', 'home_loan', 'complaint_details', 'construction_material',
        'commission_percentage', 'after_agreement_of_sale_what_is_payout_time_period',
        'is_lead_registration_required_before_site_visit', 'turnaround_time_for_lead_acknowledgement',
        'is_there_validity_period_for_registered_lead', 'accepted_modes_of_lead_registration',
        'status', 'useremail', 'poc_name', 'poc_contact', 'poc_role', 'createdat', 'updatedat',
        'verified', 'areaname', 'pricesheet_link', 'pricesheet_link_1', 'total_buildup_area',
        'uds', 'fsi', 'main_door_height', 'available_banks_for_loan', 'floor_rise_charges',
        'floor_rise_amount_per_floor', 'floor_rise_applicable_above_floor_no', 'facing_charges',
        'preferential_location_charges', 'preferential_location_charges_conditions', 'project_status',
        'google_place_id', 'google_place_name', 'google_place_address', 'google_place_location',
        'google_place_rating', 'google_place_user_ratings_total', 'google_maps_location',
        'google_place_raw_data', 'hospitals_count', 'shopping_malls_count', 'schools_count',
        'restaurants_count', 'restaurants_above_4_stars_count', 'supermarkets_count',
        'it_offices_count', 'metro_stations_count', 'railway_stations_count', 'nearest_hospitals',
        'nearest_shopping_malls', 'nearest_schools', 'nearest_restaurants', 'high_rated_restaurants',
        'nearest_supermarkets', 'nearest_it_offices', 'nearest_metro_station', 'nearest_railway_station',
        'nearest_orr_access', 'connectivity_score', 'amenities_score', 'amenities_raw_data',
        'amenities_updated_at', 'mobile_google_map_url', 'grid_score', 'isavailable',
        'configsoldoutstatus', 'city', 'state', 'cp', 'builder_age', 'builder_completed_properties',
        'builder_ongoing_projects', 'builder_operating_locations', 'builder_origin_city',
        'builder_total_properties', 'builder_upcoming_properties', 'alternative_contact', 'tier',
        'project_update_status', 'source_of_information', 'is_landlord_share', 'landlord_poc_name',
        'landlord_poc_contact', 'price_per_sft_update_date', 'configuration_update_date',
        'landlord_investor_update_date', 'images'
    ]
    
    # Filter columns that exist in dataframe
    available_columns = [col for col in expected_columns if col in df_clean.columns]
    
    # Prepare SQL
    columns_str = ','.join([f'"{col}"' for col in available_columns])
    placeholders = ','.join(['%s'] * len(available_columns))
    
    insert_sql = f"""
    INSERT INTO properties_final ({columns_str})
    VALUES ({placeholders})
    """
    
    successful_inserts = 0
    
    # Insert in batches
    for i in range(0, total_rows, batch_size):
        batch_end = min(i + batch_size, total_rows)
        batch_data = df_clean.iloc[i:batch_end]
        
        # Convert to list of tuples for available columns only
        values = []
        for _, row in batch_data.iterrows():
            row_values = tuple(row[col] for col in available_columns)
            values.append(row_values)
        
        try:
            cur.executemany(insert_sql, values)
            conn.commit()
            successful_inserts += len(values)
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            conn.rollback()
    
    cur.close()
    return successful_inserts

def main():
    print("Starting COMPLETE CSV to PostgreSQL conversion...")
    
    # Connect to database and create table
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("Creating table...")
    create_table_sql = create_simple_table()
    cur.execute(create_table_sql)
    conn.commit()
    print("✅ Table 'properties_final' created successfully")
    
    # Read CSV in chunks
    print("Reading complete CSV file...")
    chunk_size = 1000
    total_inserted = 0
    chunk_count = 0
    
    try:
        for chunk_num, df_chunk in enumerate(pd.read_csv('database_tables/final.csv', chunksize=chunk_size)):
            chunk_count += 1
            print(f"Processing chunk {chunk_count} ({len(df_chunk)} rows)...")
            
            # Clean data
            df_clean = clean_data_simple(df_chunk)
            
            # Insert data
            inserted = insert_data_simple(conn, df_clean, batch_size=100)
            total_inserted += inserted
            
            if chunk_count % 5 == 0:  # Progress update every 5 chunks
                print(f"✅ Processed {chunk_count} chunks. Total inserted: {total_inserted}")
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
    
    # Verify insertion
    cur.execute("SELECT COUNT(*) FROM properties_final")
    count = cur.fetchone()[0]
    print(f"✅ Successfully inserted {count} rows into properties_final table")
    
    # Show sample data
    cur.execute("SELECT projectname, areaname, city, price_per_sft FROM properties_final LIMIT 10")
    sample_data = cur.fetchall()
    print(f"\nSample data from properties_final:")
    for i, row in enumerate(sample_data, 1):
        print(f"  {i}. {row[0]} | {row[1]} | {row[2]} | ₹{row[3]}/sqft")
    
    # Create indexes
    print("\nCreating indexes...")
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_properties_final_areaname ON properties_final(areaname);',
        'CREATE INDEX IF NOT EXISTS idx_properties_final_city ON properties_final(city);',
        'CREATE INDEX IF NOT EXISTS idx_properties_final_projectname ON properties_final(projectname);',
        'CREATE INDEX IF NOT EXISTS idx_properties_final_buildername ON properties_final(buildername);',
        'CREATE INDEX IF NOT EXISTS idx_properties_final_status ON properties_final(status);'
    ]
    
    for index_sql in indexes:
        try:
            cur.execute(index_sql)
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not create index: {e}")
    
    print("✅ Indexes created")
    
    # Show statistics
    cur.execute("SELECT city, COUNT(*) as count FROM properties_final WHERE city IS NOT NULL GROUP BY city ORDER BY count DESC LIMIT 10")
    city_stats = cur.fetchall()
    print(f"\nTop cities by property count:")
    for city, count in city_stats:
        print(f"  {city}: {count} properties")
    
    cur.close()
    conn.close()
    
    print(f"\n🎉 Complete CSV conversion finished! Total records: {count}")

if __name__ == "__main__":
    main()