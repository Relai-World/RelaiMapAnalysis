"""
Import script: unified_data_DataType_Raghu_rows.csv -> PostgreSQL
Table: real_estate_projects
"""
import os
import sys
import csv
import json
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname":   os.getenv("DB_NAME", "real_estate_intelligence"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "post@123"),
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
}

CSV_PATH = r"c:\Users\gudde\OneDrive\Desktop\Final\unified_data_DataType_Raghu_rows.csv"
TABLE_NAME = "real_estate_projects"

# ---------------------------------------------------------------------------
# Column type map — inferred from the CSV structure
# ---------------------------------------------------------------------------
COLUMN_TYPES = {
    "id":                                          "INTEGER",
    "rera_number":                                 "TEXT",
    "projectname":                                 "TEXT",
    "buildername":                                 "TEXT",
    "baseprojectprice":                            "BIGINT",
    "projectbrochure":                             "TEXT",
    "projectlocation":                             "TEXT",
    "project_type":                                "TEXT",
    "communitytype":                               "TEXT",
    "total_land_area":                             "NUMERIC",
    "number_of_towers":                            "INTEGER",
    "number_of_floors":                            "INTEGER",
    "number_of_flats_per_floor":                   "INTEGER",
    "total_number_of_units":                       "INTEGER",
    "project_launch_date":                         "TEXT",
    "possession_date":                             "TEXT",
    "construction_status":                         "TEXT",
    "open_space":                                  "NUMERIC",
    "carpet_area_percentage":                      "NUMERIC",
    "floor_to_ceiling_height":                     "NUMERIC",
    "price_per_sft":                               "INTEGER",
    "external_amenities":                          "TEXT",
    "specification":                               "TEXT",
    "powerbackup":                                 "TEXT",
    "no_of_passenger_lift":                        "TEXT",
    "no_of_service_lift":                          "TEXT",
    "visitor_parking":                             "TEXT",
    "ground_vehicle_movement":                     "TEXT",
    "bhk":                                         "TEXT",
    "facing":                                      "TEXT",
    "sqfeet":                                      "INTEGER",
    "sqyard":                                      "TEXT",
    "no_of_car_parkings":                          "TEXT",
    "amount_for_extra_car_parking":                "TEXT",
    "home_loan":                                   "TEXT",
    "complaint_details":                           "TEXT",
    "construction_material":                       "TEXT",
    "commission_percentage":                       "TEXT",
    "after_agreement_of_sale_what_is_payout_time_period": "TEXT",
    "is_lead_registration_required_before_site_visit":    "TEXT",
    "turnaround_time_for_lead_acknowledgement":    "TEXT",
    "is_there_validity_period_for_registered_lead":"TEXT",
    "accepted_modes_of_lead_registration":         "TEXT",
    "status":                                      "TEXT",
    "useremail":                                   "TEXT",
    "poc_name":                                    "TEXT",
    "poc_contact":                                 "TEXT",
    "poc_role":                                    "TEXT",
    "createdat":                                   "TEXT",
    "updatedat":                                   "TEXT",
    "verified":                                    "TEXT",
    "areaname":                                    "TEXT",
    "pricesheet_link":                             "TEXT",
    "pricesheet_link_1":                           "TEXT",
    "total_buildup_area":                          "NUMERIC",
    "uds":                                         "NUMERIC",
    "fsi":                                         "NUMERIC",
    "main_door_height":                            "TEXT",
    "available_banks_for_loan":                    "TEXT",
    "floor_rise_charges":                          "TEXT",
    "floor_rise_amount_per_floor":                 "TEXT",
    "floor_rise_applicable_above_floor_no":        "TEXT",
    "facing_charges":                              "TEXT",
    "preferential_location_charges":               "TEXT",
    "preferential_location_charges_conditions":    "TEXT",
    "project_status":                              "TEXT",
    "google_place_id":                             "TEXT",
    "google_place_name":                           "TEXT",
    "google_place_address":                        "TEXT",
    "google_place_location":                       "TEXT",
    "google_place_rating":                         "NUMERIC",
    "google_place_user_ratings_total":             "INTEGER",
    "google_maps_location":                        "TEXT",
    "google_place_raw_data":                       "TEXT",
    "hospitals_count":                             "INTEGER",
    "shopping_malls_count":                        "INTEGER",
    "schools_count":                               "INTEGER",
    "restaurants_count":                           "INTEGER",
    "restaurants_above_4_stars_count":             "INTEGER",
    "supermarkets_count":                          "INTEGER",
    "it_offices_count":                            "INTEGER",
    "metro_stations_count":                        "INTEGER",
    "railway_stations_count":                      "INTEGER",
    "nearest_hospitals":                           "TEXT",
    "nearest_shopping_malls":                      "TEXT",
    "nearest_schools":                             "TEXT",
    "nearest_restaurants":                         "TEXT",
    "high_rated_restaurants":                      "TEXT",
    "nearest_supermarkets":                        "TEXT",
    "nearest_it_offices":                          "TEXT",
    "nearest_metro_station":                       "TEXT",
    "nearest_railway_station":                     "TEXT",
    "nearest_orr_access":                          "TEXT",
    "connectivity_score":                          "NUMERIC",
    "amenities_score":                             "NUMERIC",
    "amenities_raw_data":                          "TEXT",
    "amenities_updated_at":                        "TEXT",
    "mobile_google_map_url":                       "TEXT",
    "grid_score":                                  "NUMERIC",
    "isavailable":                                 "TEXT",
    "configsoldoutstatus":                         "TEXT",
    "city":                                        "TEXT",
    "state":                                       "TEXT",
    "cp":                                          "TEXT",
    "builder_age":                                 "TEXT",
    "builder_completed_properties":                "TEXT",
    "builder_ongoing_projects":                    "TEXT",
    "builder_operating_locations":                 "TEXT",
    "builder_origin_city":                         "TEXT",
    "builder_total_properties":                    "TEXT",
    "builder_upcoming_properties":                 "TEXT",
    "alternative_contact":                         "TEXT",
    "tier":                                        "TEXT",
    "project_update_status":                       "TEXT",
    "source_of_information":                       "TEXT",
    "is_landlord_share":                           "TEXT",
    "landlord_poc_name":                           "TEXT",
    "landlord_poc_contact":                        "TEXT",
    "price_per_sft_update_date":                   "TEXT",
    "configuration_update_date":                   "TEXT",
    "landlord_investor_update_date":               "TEXT",
    "images":                                      "TEXT",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_val(val, col_type):
    """Convert empty strings to None and coerce types as needed."""
    v = val.strip() if val else ""
    if v == "" or v.lower() in ("null", "none", "nan"):
        return None
    try:
        if col_type in ("INTEGER", "BIGINT"):
            return int(float(v))
        if col_type == "NUMERIC":
            return float(v)
        if col_type == "TIMESTAMPTZ":
            return v  # psycopg2 handles ISO strings
    except (ValueError, TypeError):
        return None
    return v  # TEXT


def normalise_header(h):
    """Lower-case and replace spaces/slashes to match COLUMN_TYPES keys."""
    return (
        h.strip()
         .lower()
         .replace(" ", "_")
         .replace("/", "_")
         .replace("-", "_")
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"[+] Connecting to PostgreSQL …")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # ---- 1. Read headers from CSV ----------------------------------------
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        raw_headers = next(reader)

    headers = [normalise_header(h) for h in raw_headers]
    print(f"[+] {len(headers)} columns detected")

    # Columns not in our explicit map → TEXT
    col_defs = []
    for h in headers:
        t = COLUMN_TYPES.get(h, "TEXT")
        col_defs.append(f'"{h}" {t}')

    # ---- 2. Create table (DROP IF EXISTS for clean import) ---------------
    drop_sql  = f'DROP TABLE IF EXISTS "{TABLE_NAME}";'
    create_sql = (
        f'CREATE TABLE "{TABLE_NAME}" (\n  '
        + ",\n  ".join(col_defs)
        + "\n);"
    )

    print(f"[+] Creating table '{TABLE_NAME}' …")
    cur.execute(drop_sql)
    cur.execute(create_sql)
    conn.commit()
    print("[+] Table created successfully.")

    # ---- 3. Bulk-insert rows ---------------------------------------------
    col_names = [f'"{h}"' for h in headers]
    placeholders = ", ".join(["%s"] * len(headers))
    insert_sql = (
        f'INSERT INTO "{TABLE_NAME}" ({", ".join(col_names)}) '
        f"VALUES ({placeholders})"
    )

    col_types = [COLUMN_TYPES.get(h, "TEXT") for h in headers]

    BATCH = 500
    rows_buf = []
    total_inserted = 0
    total_skipped  = 0

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for i, row in enumerate(reader, start=1):
            if len(row) != len(headers):
                total_skipped += 1
                continue

            try:
                coerced = [safe_val(v, t) for v, t in zip(row, col_types)]
                rows_buf.append(coerced)
            except Exception as e:
                print(f"  [!] Row {i}: coercion error – {e}")
                total_skipped += 1
                continue

            if len(rows_buf) >= BATCH:
                try:
                    execute_batch(cur, insert_sql, rows_buf, page_size=BATCH)
                    conn.commit()
                    total_inserted += len(rows_buf)
                    print(f"  … {total_inserted:,} rows inserted", end="\r")
                except Exception as e:
                    conn.rollback()
                    print(f"\n  [!] Batch error near row {i}: {e}")
                rows_buf = []

    # flush remainder
    if rows_buf:
        try:
            execute_batch(cur, insert_sql, rows_buf, page_size=BATCH)
            conn.commit()
            total_inserted += len(rows_buf)
        except Exception as e:
            conn.rollback()
            print(f"\n  [!] Final batch error: {e}")

    cur.close()
    conn.close()

    print(f"\n[✓] Done! Inserted {total_inserted:,} rows | Skipped {total_skipped} rows")
    print(f"[✓] Table: {TABLE_NAME}")


if __name__ == "__main__":
    main()
