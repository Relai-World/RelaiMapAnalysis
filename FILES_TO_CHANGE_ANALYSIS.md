# Files Using psycopg2 - Which Need Changes?

## 🔴 CRITICAL - MUST CHANGE (Production Code) - 4 files

### 1. api.py
**Purpose**: Main API server (FastAPI)  
**Used by**: Frontend in production  
**Must change**: YES - This is your live API

### 2. aggregation/compute_location_insights.py
**Purpose**: Computes sentiment/growth/investment scores  
**Used by**: Backend data processing  
**Must change**: YES - If you run this for data updates

### 3. aggregation/fetch_infra_data.py
**Purpose**: Fetches infrastructure data  
**Used by**: Backend data processing  
**Must change**: YES - If you run this for data updates

### 4. aggregation/generate_smart_facts.py
**Purpose**: Generates smart facts for locations  
**Used by**: Backend data processing  
**Must change**: YES - If you run this for data updates

---

## 🟡 MAYBE CHANGE (Data Update Scripts) - 2 files

### 5. update_price_trends.py
**Purpose**: Updates price trends table  
**Used by**: Manual data updates  
**Must change**: MAYBE - If you update price data

### 6. update_price_trends_new.py
**Purpose**: Alternative price trends updater  
**Used by**: Manual data updates  
**Must change**: MAYBE - If you use this

---

## 🟢 UTILITY/DEBUG - DON'T NEED TO CHANGE - 44 files

### Check/Debug Scripts (20 files)
- check_corpus.py
- check_db_status.py
- check_db_tables.py
- check_depalle_details.py
- check_fk.py
- check_locations_schema.py
- check_location_costs_schema.py
- check_map_locations.py
- check_news_table.py
- check_price_trends_schema.py
- check_property_data.py
- check_property_filtering.py
- check_registration_table.py
- check_sentiment_coverage.py
- check_sentiment_values.py
- debug_bhk_values.py
- debug_db.py
- debug_location_matching.py
- test_connection_variations.py
- test_direct_connection.py

### Data Migration/Export Scripts (10 files)
- convert_final_csv_complete.py
- export_location_costs_csv.py
- export_news_to_csv.py
- export_specific_tables.py
- export_tables_to_csv.py
- migrate_to_supabase.py
- migrate_to_supabase_simple.py
- import_raghu_data.py
- recreate_price_trends_table.py
- setup_rishikacode.py

### Location Management Scripts (7 files)
- find_low_count_locations.py
- find_zero_record_locations.py
- fix_all_locations.py
- fix_db_locations.py
- fix_locations_interactive.py
- fix_location_spellings.py
- interactive_location_manager.py
- list_all_locations.py
- merge_duplicate_locations.py
- get_unique_locations.py

### Scraper Scripts (7 files)
- scraper/base_scraper.py
- scraper/bhubharati_authenticated_scraper.py
- scraper/bhubharati_dashboard_scraper.py
- scraper/bhubharati_data_extractor.py
- registrationandstamps/igrs_scraper_v2.py
- sentiment/main_sentiment.py

---

## 📊 SUMMARY

### Must Change (Production): 4 files
1. api.py
2. aggregation/compute_location_insights.py
3. aggregation/fetch_infra_data.py
4. aggregation/generate_smart_facts.py

### Maybe Change (If You Use): 2 files
5. update_price_trends.py
6. update_price_trends_new.py

### Don't Need to Change: 44 files
- All check/debug scripts
- All migration/export scripts
- All location management scripts
- All scraper scripts

---

## 🎯 RECOMMENDATION

**Change only 4-6 files** (the production ones)

The rest are utility scripts you run manually for debugging/maintenance. They can keep using the old connection method or you can just get the correct password and they'll all work.

---

## ⚠️ IMPORTANT DECISION

### Option 1: Get Correct Password (EASIEST)
- Just get the right password from Supabase
- Update `.env` file
- ALL 50+ files work immediately
- No code changes needed

### Option 2: Rewrite to Supabase REST API
- Change 4-6 production files
- Complex SQL queries won't work (CTEs, JOINs, PostGIS)
- Need to rewrite query logic
- More work, less features

**I strongly recommend Option 1** - Just get the correct password!

---

## 🔍 Which Files Do You Actually Run?

Tell me which of these you actually use:
- ✅ api.py (YES - your main API)
- ❓ aggregation scripts (do you run these?)
- ❓ update_price_trends (do you run this?)
- ❓ scrapers (do you run these?)

Then we'll know exactly what needs changing.
