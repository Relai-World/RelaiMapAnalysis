# Future Development Scraper - Supabase Edition

## Overview

This scraper collects news articles about future developments in Hyderabad locations (2022-2026) and stores them in Supabase.

## Changes Made

### ✅ Updated to use Supabase
- Replaced PostgreSQL with Supabase client
- Fetches locations dynamically from `locations` table
- Stores scraped data in `future_development_scrap` table

### ✅ Key Features
- Scrapes Google News for future development articles
- Targets 20 articles per location
- Extracts year mentions (2022-2026)
- Filters articles that mention the location
- Avoids duplicates by checking URL

## Setup

### 1. Create the Table in Supabase

Run this SQL in Supabase SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS future_development_scrap (
    id BIGSERIAL PRIMARY KEY,
    location_id INTEGER,
    location_name VARCHAR(255),
    source VARCHAR(255),
    url TEXT UNIQUE,
    content TEXT,
    published_at TIMESTAMP,
    year_mentioned INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_url_future_dev UNIQUE(url)
);

CREATE INDEX IF NOT EXISTS idx_future_dev_location_id ON future_development_scrap(location_id);
CREATE INDEX IF NOT EXISTS idx_future_dev_year ON future_development_scrap(year_mentioned);

ALTER TABLE future_development_scrap 
ADD CONSTRAINT fk_future_dev_location 
FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE;
```

Or run the file: `create_future_development_table.sql`

### 2. Install Dependencies

```bash
pip install playwright beautifulsoup4 feedparser supabase requests python-dotenv
playwright install chromium
```

### 3. Configure Environment

Make sure your `.env` file has:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 4. Run the Scraper

```bash
python scraper/scrape_future_dev.py
```

## How It Works

1. **Fetches Locations**: Queries Supabase `locations` table for all Hyderabad locations
2. **Searches News**: Uses 10 different future development queries per location
3. **Scrapes Articles**: Uses Playwright to fetch full article content
4. **Filters Content**: Only saves articles that mention the location
5. **Extracts Years**: Identifies year mentions (2022-2026)
6. **Stores Data**: Saves to `future_development_scrap` table in Supabase

## Query Types

The scraper uses these query variations:
- Upcoming projects OR future development OR planned infrastructure
- Metro expansion OR new metro line OR metro station opening
- Upcoming mall OR new shopping center OR commercial development
- Road widening OR flyover construction OR infrastructure project
- IT park OR tech hub OR business park development
- Residential project OR apartment launch OR housing development
- Hospital expansion OR new medical facility OR healthcare infrastructure
- School opening OR educational institution OR university campus
- Airport expansion OR connectivity improvement OR transport development
- Smart city project OR GHMC development OR municipal infrastructure

## Configuration

Edit these variables in the script:

```python
ARTICLES_PER_LOCATION = 20  # Target articles per location
```

## Output

Data is stored in `future_development_scrap` table with:
- `location_id`: ID from locations table
- `location_name`: Name of the location
- `source`: News source
- `url`: Article URL (unique)
- `content`: Full article text (up to 5000 chars)
- `published_at`: Publication date
- `year_mentioned`: Extracted year (2022-2026)
- `scraped_at`: When the article was scraped

## Monitoring

The scraper provides real-time progress:
- Current location being processed
- Articles found per query
- Articles saved vs skipped
- Total articles in database

## Notes

- Scraper skips locations that already have 20+ articles
- Uses random delays to avoid rate limiting
- Headless browser for JavaScript-heavy sites
- Duplicate URLs are automatically skipped
