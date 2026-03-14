# Detailed Table Interconnections Analysis

## Executive Summary

Your database has **6 core tables** with **3 direct foreign key relationships** and **2 name-based fuzzy relationships**. All tables are interconnected through the `locations` table as the master reference.

---

## Core Tables & Their Relationships

### 1. **locations** (Master Reference Table)
**Purpose**: Central registry of all geographic locations in Hyderabad

**Schema**:
```sql
- id (PRIMARY KEY)
- name (VARCHAR)
- geom (GEOMETRY/POINT) - PostGIS spatial data
- boundary (GEOMETRY/POLYGON) - Optional boundary data
```

**Relationships**:
- **Parent to**: `news_balanced_corpus_1`, `location_insights`, `location_costs`
- **Referenced by**: `price_trends` (via name), `unified_data_DataType_Raghu` (via areaname)

**Used in Files**:
- `api.py` - All endpoints use this as base
- `aggregation/compute_location_insights.py` - Loops through all locations
- `aggregation/fetch_infra_data.py` - Gets coordinates for each location
- `aggregation/generate_smart_facts.py` - Generates summaries per location

---

### 2. **news_balanced_corpus_1** (News & Sentiment Data)
**Purpose**: Stores scraped news articles with sentiment analysis

**Schema**:
```sql
- id (PRIMARY KEY)
- location_id (FOREIGN KEY → locations.id)
- location_name (VARCHAR)
- source (VARCHAR) - e.g., 'Google News', 'Reddit'
- url (TEXT)
- content (TEXT)
- published_at (TIMESTAMP)
- category (VARCHAR)
- sentiment_score (FLOAT) - Range: -1 to 1
- sentiment_label (VARCHAR) - 'positive', 'negative', 'neutral'
- confidence (FLOAT)
- scraped_at (TIMESTAMP)
```

**Relationships**:
- **Child of**: `locations` (via `location_id`)
- **Feeds into**: `location_insights` (aggregated sentiment data)

**How It's Linked**:
```sql
-- Direct foreign key relationship
SELECT * FROM news_balanced_corpus_1 
WHERE location_id = <locations.id>
```

**Used in Files**:
- `api.py`:
  - `/api/v1/insights` - Counts articles per location
  - `/api/v1/search` - Searches location names
- `aggregation/compute_location_insights.py` - Aggregates sentiment scores
- `scraper/scrape_to_csv_batch2.py` - Inserts new articles
- `scraper/scrape_playwright.py` - Inserts scraped data
- `scraper/scrape_reddit_targeted.py` - Inserts Reddit posts

**Key Queries**:
```sql
-- Count articles per location
SELECT location_id, COUNT(*) as article_count
FROM news_balanced_corpus_1 
GROUP BY location_id

-- Average sentiment per location
SELECT location_id, AVG(sentiment_score) as avg_sentiment
FROM news_balanced_corpus_1
WHERE sentiment_score IS NOT NULL
GROUP BY location_id
```

---

### 3. **location_insights** (Aggregated Scores)
**Purpose**: Stores computed sentiment, growth, and investment scores per location

**Schema**:
```sql
- location_id (PRIMARY KEY, FOREIGN KEY → locations.id)
- avg_sentiment_score (FLOAT)
- growth_score (FLOAT) - Computed from article volume + sentiment
- investment_score (FLOAT) - Computed from growth + sentiment
- sentiment_summary (TEXT) - Human-readable summary
- growth_summary (TEXT)
- invest_summary (TEXT)
- last_updated (TIMESTAMP)
```

**Relationships**:
- **Child of**: `locations` (via `location_id`)
- **Computed from**: `news_balanced_corpus_1`, `price_trends`, `location_infrastructure` (deprecated)

**How It's Linked**:
```sql
-- One-to-one relationship with locations
SELECT l.*, li.avg_sentiment_score, li.growth_score, li.investment_score
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id
```

**Used in Files**:
- `api.py`:
  - `/api/v1/insights` - Main endpoint showing all scores
- `aggregation/compute_location_insights.py` - **CREATES/UPDATES** this table
  - Calculates growth_score from article count + sentiment
  - Calculates investment_score from growth + sentiment
  - Uses UPSERT (INSERT ... ON CONFLICT)
- `aggregation/generate_smart_facts.py` - Updates summary text fields

**Computation Logic** (from `compute_location_insights.py`):
```python
# Growth Score = 80% article volume + 20% sentiment
buzz = log(article_count + 1, 10)  # Logarithmic scale
buzz_normalized = clamp(buzz / 3.5)
sentiment_normalized = clamp(avg_sentiment + 0.5)
growth_score = (0.8 * buzz_normalized) + (0.2 * sentiment_normalized)

# Investment Score = 70% growth + 30% sentiment
investment_score = (0.7 * growth_score) + (0.3 * sentiment_normalized)
```

---

### 4. **price_trends** (Historical Price Data)
**Purpose**: Stores property price trends from 2020-2026

**Schema**:
```sql
- id (PRIMARY KEY)
- location (VARCHAR) - Location name (NOT ID!)
- year_2020 (INTEGER) - Price per sqft
- year_2021 (INTEGER)
- year_2022 (INTEGER)
- year_2023 (INTEGER)
- year_2024 (INTEGER)
- year_2025 (INTEGER)
- year_2026 (INTEGER)
```

**Relationships**:
- **Linked to**: `locations` via **NAME MATCHING** (not foreign key!)
- **Match Logic**: `LOWER(price_trends.location) = LOWER(locations.name)`

**How It's Linked**:
```sql
-- Name-based join (case-insensitive)
SELECT l.id, l.name, pt.year_2020, pt.year_2021, ...
FROM locations l
LEFT JOIN price_trends pt ON LOWER(pt.location) = LOWER(l.name)
```

**Used in Files**:
- `api.py`:
  - `/api/v1/location/{id}/trends` - Gets trends for specific location
  - `/api/v1/market-trends` - Average across all locations
- `aggregation/generate_smart_facts.py` - Calculates CAGR for investment summary
- `update_price_trends.py` - **POPULATES** this table with hardcoded data
- `update_price_trends_new.py` - **POPULATES** with extended dataset

**Key Calculations**:
```python
# Year-over-Year Growth
growth_yoy = ((current_year - previous_year) / previous_year) * 100

# CAGR (Compound Annual Growth Rate)
years_span = end_year - start_year
cagr = (pow(end_price / start_price, 1/years_span) - 1) * 100
```

---

### 5. **unified_data_DataType_Raghu** (Property Listings)
**Purpose**: Real estate property listings with detailed information

**Schema** (80+ columns, key ones):
```sql
- id (PRIMARY KEY)
- projectname (VARCHAR)
- buildername (VARCHAR)
- areaname (VARCHAR) - Links to locations.name via FUZZY MATCH
- city (VARCHAR)
- state (VARCHAR)
- price_per_sft (VARCHAR/NUMERIC)
- baseprojectprice (VARCHAR/NUMERIC)
- bhk (VARCHAR) - e.g., '2', '3', '4'
- sqfeet (VARCHAR)
- sqyard (VARCHAR)
- facing (VARCHAR)
- project_type (VARCHAR)
- construction_status (VARCHAR)
- possession_date (DATE)
- images (TEXT)
- google_place_location (VARCHAR)
- google_place_rating (VARCHAR)
- rera_number (VARCHAR)
... (70+ more columns)
```

**Relationships**:
- **Linked to**: `locations` via **FUZZY NAME MATCHING** (not foreign key!)
- **Match Logic**: Multiple strategies for handling name variations

**How It's Linked** (Fuzzy Matching):
```sql
-- Multi-strategy fuzzy matching
SELECT * FROM unified_data_DataType_Raghu p
JOIN locations l ON (
    -- Exact match (case-insensitive)
    LOWER(p.areaname) = LOWER(l.name)
    -- Match without spaces
    OR LOWER(REPLACE(p.areaname, ' ', '')) = LOWER(REPLACE(l.name, ' ', ''))
    -- Starts with location name
    OR p.areaname ILIKE l.name || ', %'
    -- Contains location name
    OR l.name ILIKE p.areaname
)
```

**Fuzzy Matching Examples**:
- "HITEC City" matches "Hitec City"
- "Appa Junction" matches "AppaJunction"
- "Gachibowli, Hyderabad" matches "Gachibowli"

**Used in Files**:
- `api.py`:
  - `/api/v1/insights` - Aggregates property prices per location
  - `/api/v1/location-costs` - Property cost statistics
  - `/api/v1/property-costs` - All property costs
  - `/api/v1/properties?area=X` - Search properties by area
  - `/api/v1/properties/{id}` - Get single property details

**Key Aggregations**:
```sql
-- Average price per location
SELECT 
    l.name,
    COUNT(*) as property_count,
    AVG(CAST(price_per_sft AS NUMERIC)) as avg_price,
    MIN(CAST(price_per_sft AS NUMERIC)) as min_price,
    MAX(CAST(price_per_sft AS NUMERIC)) as max_price
FROM unified_data_DataType_Raghu p
JOIN locations l ON <fuzzy_match>
GROUP BY l.name
```

---

### 6. **location_costs** (Property Cost Statistics)
**Purpose**: Pre-computed property cost statistics per location

**Schema**:
```sql
- id (PRIMARY KEY)
- location_id (FOREIGN KEY → locations.id)
- avg_price_per_sft (NUMERIC)
- min_price_per_sft (NUMERIC)
- max_price_per_sft (NUMERIC)
- avg_base_price (NUMERIC)
- property_count (INTEGER)
- last_updated (TIMESTAMP)
```

**Relationships**:
- **Child of**: `locations` (via `location_id`)
- **Computed from**: `unified_data_DataType_Raghu` (aggregated)

**How It's Linked**:
```sql
-- Direct foreign key relationship
SELECT l.*, lc.avg_price_per_sft, lc.property_count
FROM locations l
LEFT JOIN location_costs lc ON lc.location_id = l.id
```

**Used in Files**:
- `api.py`:
  - `/api/v1/location-costs` - Gets all location costs
  - `/api/v1/location-costs/{name}` - Gets specific location costs

**Note**: This table appears to be **redundant** - the same data is computed on-the-fly from `unified_data_DataType_Raghu` in most endpoints. It may be used for caching/performance.

---

## Deprecated/Removed Tables

### ❌ location_infrastructure
**Status**: Referenced in code but **NOT in Supabase schema**

**Was used for**:
- Storing infrastructure counts (hospitals, schools, metro, airports)
- Referenced in `aggregation/generate_smart_facts.py`
- Referenced in `aggregation/fetch_infra_data.py`

**Current workaround**: Growth facts use default text instead of infrastructure data

---

## Complete Relationship Diagram

```
                    ┌─────────────────────┐
                    │     locations       │
                    │   (Master Table)    │
                    │  - id (PK)          │
                    │  - name             │
                    │  - geom (PostGIS)   │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┬──────────────┐
                │              │              │              │
                │ (FK)         │ (FK)         │ (FK)         │ (name match)
                ▼              ▼              ▼              ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ news_balanced_   │ │  location_   │ │  location_   │ │ price_trends │
    │ corpus_1         │ │  insights    │ │  costs       │ │              │
    │ - location_id(FK)│ │ - location_id│ │ - location_id│ │ - location   │
    │ - sentiment_score│ │ - avg_sent   │ │ - avg_price  │ │ - year_2020  │
    │ - content        │ │ - growth     │ │ - min_price  │ │ - year_2021  │
    │ - published_at   │ │ - investment │ │ - max_price  │ │ - ...        │
    └──────────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                │                                                    
                │ (aggregated)                                       
                └──────────────────────────────────────┐            
                                                       │            
                                                       ▼            
                                            ┌──────────────────┐   
                                            │ location_insights│   
                                            │ (computed scores)│   
                                            └──────────────────┘   

                    ┌─────────────────────┐
                    │     locations       │
                    │  - name             │
                    └──────────┬──────────┘
                               │
                               │ (fuzzy name match)
                               ▼
                    ┌──────────────────────────┐
                    │ unified_data_DataType_   │
                    │ Raghu                    │
                    │ - areaname (fuzzy match) │
                    │ - projectname            │
                    │ - price_per_sft          │
                    │ - bhk, sqfeet, etc.      │
                    └──────────────────────────┘
                               │
                               │ (aggregated)
                               ▼
                    ┌──────────────────────┐
                    │  location_costs      │
                    │  (cached aggregates) │
                    └──────────────────────┘
```

---

## Data Flow & Dependencies

### 1. **News Scraping → Sentiment Analysis**
```
Scrapers → news_balanced_corpus_1 → compute_location_insights.py → location_insights
```

**Files involved**:
- `scraper/scrape_to_csv_batch2.py` - Scrapes Google News
- `scraper/scrape_playwright.py` - Scrapes with browser automation
- `scraper/scrape_reddit_targeted.py` - Scrapes Reddit
- `aggregation/compute_location_insights.py` - Computes scores

### 2. **Price Trends Loading**
```
CSV/Hardcoded Data → update_price_trends.py → price_trends table
```

**Files involved**:
- `update_price_trends.py` - Loads 120+ locations
- `update_price_trends_new.py` - Loads 200+ locations (extended)

### 3. **Property Data → Location Aggregation**
```
unified_data_DataType_Raghu → (fuzzy match) → locations → aggregated in API
```

**Files involved**:
- `api.py` - All property-related endpoints
- Fuzzy matching happens in SQL queries (no separate script)

### 4. **Infrastructure Data (Deprecated)**
```
Overpass API → fetch_infra_data.py → location_infrastructure (NOT IN SUPABASE)
```

**Status**: This flow is broken - table doesn't exist in Supabase

---

## Critical Interconnection Points

### Point 1: location_id (Foreign Key)
**Tables**: `news_balanced_corpus_1`, `location_insights`, `location_costs`

**Integrity**: ✅ Strong - Direct foreign key relationships

**Usage**: All queries use `WHERE location_id = X` or `JOIN ON location_id`

### Point 2: location name (Exact Match)
**Tables**: `locations.name` ↔ `price_trends.location`

**Integrity**: ⚠️ Medium - Depends on exact name matching (case-insensitive)

**Potential Issues**:
- Name typos will break the link
- Name changes in `locations` won't update `price_trends`

### Point 3: areaname (Fuzzy Match)
**Tables**: `locations.name` ↔ `unified_data_DataType_Raghu.areaname`

**Integrity**: ⚠️ Weak - Relies on fuzzy matching logic

**Potential Issues**:
- New name variations may not match
- Multiple locations could match same areaname
- Performance impact (no indexes on fuzzy match)

---

## Recommendations

### 1. Add Foreign Keys to price_trends
```sql
ALTER TABLE price_trends 
ADD COLUMN location_id INTEGER REFERENCES locations(id);

-- Populate from name matching
UPDATE price_trends pt
SET location_id = l.id
FROM locations l
WHERE LOWER(pt.location) = LOWER(l.name);
```

### 2. Add location_id to unified_data_DataType_Raghu
```sql
ALTER TABLE unified_data_DataType_Raghu
ADD COLUMN location_id INTEGER REFERENCES locations(id);

-- Populate using fuzzy matching logic
UPDATE unified_data_DataType_Raghu p
SET location_id = l.id
FROM locations l
WHERE LOWER(p.areaname) = LOWER(l.name)
   OR LOWER(REPLACE(p.areaname, ' ', '')) = LOWER(REPLACE(l.name, ' ', ''));
```

### 3. Remove or Populate location_costs
Either:
- **Option A**: Drop the table (data is computed on-the-fly anyway)
- **Option B**: Create a scheduled job to populate it for caching

### 4. Handle Missing location_infrastructure
Either:
- **Option A**: Remove references from code
- **Option B**: Create the table in Supabase and populate it

---

## Summary Statistics

**Total Tables**: 6 core tables
**Foreign Key Relationships**: 3 (via location_id)
**Name-Based Relationships**: 2 (exact + fuzzy)
**Deprecated Tables**: 1 (location_infrastructure)

**Data Integrity**:
- ✅ Strong: news_balanced_corpus_1, location_insights, location_costs
- ⚠️ Medium: price_trends (name matching)
- ⚠️ Weak: unified_data_DataType_Raghu (fuzzy matching)

**Files Using Interconnections**: 15+ Python files across scrapers, aggregation, and API
