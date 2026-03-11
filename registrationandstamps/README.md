# IGRS Database-Driven Scraper

Automatically scrapes property transaction data from IGRS Telangana for all locations in your database.

## Features

✅ Fetches all 170 locations from your database automatically  
✅ Scrapes data from 2019-2026 (quarterly)  
✅ Progress tracking with resume capability  
✅ Automatic checkpointing every 100 records  
✅ Data cleaning and deduplication  
✅ Comprehensive logging  

## Quick Start

```bash
# 1. Make sure Chrome is installed
# 2. Install dependencies
pip install selenium pandas psycopg2-binary python-dotenv beautifulsoup4

# 3. Run the scraper
python scrape_from_database.py
```

## How It Works

1. **Fetches Locations**: Reads all 170 Hyderabad locations from your `locations` table
2. **Iterates Through Each**: For each location, scrapes data for all quarters from 2019-2026
3. **Manual CAPTCHA**: Browser opens, you solve CAPTCHA once per search
4. **Auto-Pagination**: Automatically clicks through all result pages
5. **Progress Tracking**: Saves progress after each location/quarter
6. **Checkpointing**: Saves data every 100 records
7. **Resume Capability**: If interrupted, resumes from where it left off

## Configuration

Edit `scraper_config.json` to change:
- District (RANGAREDDY, HYDERABAD, MEDCHAL MALKAJGIRI)
- Mandal (Serilingampally, Rajendranagar, etc.)
- Date ranges
- Checkpoint intervals

## Output Files

- `data/checkpoint_*.csv` - Intermediate checkpoints
- `data/igrs_complete_YYYYMMDD.csv` - Final cleaned dataset
- `scraping_progress.json` - Progress tracker
- `igrs_scraper.log` - Detailed logs

## Data Fields Captured

- `document_number` - Unique registration ID
- `transaction_date` - Date of registration
- `village` - Location/village name
- `property_type` - Plot/Flat/House/Commercial
- `extent_area` - Area in sq.yards/sq.ft
- `sale_consideration_value` - Transaction value
- `price_per_sqft` - Calculated price per sqft
- `district`, `mandal`, `quarter` - Metadata

## Resume After Interruption

The scraper automatically resumes from where it stopped. Just run it again:

```bash
python scrape_from_database.py
```

It will skip already completed location/quarter combinations.

## Analytics

After scraping, run analytics:

```bash
python analytics.py
```

This generates:
- Price trends (quarterly/monthly/yearly)
- Volume trends
- Locality rankings
- Property type analysis
- JSON export for frontend

## Troubleshooting

**Location not found in dropdown**
- Some database locations may not exist in IGRS dropdown
- These are logged and skipped automatically

**CAPTCHA timeout**
- Default timeout is 120 seconds
- Solve CAPTCHA within this time
- Adjust in `scraper_config.json` if needed

**Browser closes unexpectedly**
- Check `igrs_scraper.log` for errors
- Progress is saved, just restart

## Progress Tracking

Check progress anytime:
```bash
cat scraping_progress.json
```

Shows:
- Completed tasks
- Failed tasks
- Total records scraped
- Locations completed

## Tips

1. **Run in batches**: Scrape 20-30 locations at a time
2. **Check logs**: Monitor `igrs_scraper.log` for issues
3. **Backup checkpoints**: Copy `data/checkpoint_*.csv` files periodically
4. **Verify data**: Check final CSV for data quality

## Example Output

```
================================================================================
🚀 DATABASE-DRIVEN IGRS SCRAPER
================================================================================

📊 Configuration:
   District: RANGAREDDY
   Mandal: Serilingampally
   Locations: 170
   Date Ranges: 32 quarters (2019-2026)
   Total Tasks: 5,440

================================================================================
📍 [1/170] Gachibowli
================================================================================
      📅 2019Q1
         📄 Page 1
         📄 Page 2
         ✅ 45 records
      📅 2019Q2
         ✅ 38 records
      ...

   📊 Progress: 1/170 locations
   📊 Total Records: 245
```
