# Database Table Relationships

## Core Tables in Supabase

### 1. **locations** (Master table)
- **Primary Key**: `id`
- **Columns**: `id`, `name`, `geom` (geometry/coordinates)
- **Purpose**: Master list of all locations with geographic data

### 2. **news_balanced_corpus_1** 
- **Foreign Key**: `location_id` → `locations.id`
- **Purpose**: News articles with sentiment analysis
- **Columns**: `id`, `location_id`, `location_name`, `content`, `sentiment_score`, `confidence`, `published_at`

### 3. **location_insights**
- **Foreign Key**: `location_id` → `locations.id`
- **Purpose**: Aggregated sentiment, growth, and investment scores
- **Columns**: `location_id`, `avg_sentiment_score`, `growth_score`, `investment_score`, `last_updated`

### 4. **price_trends**
- **Link**: Matches `locations.name` (by location name, not ID)
- **Purpose**: Historical price data from 2020-2026
- **Columns**: `location`, `year_2020`, `year_2021`, `year_2022`, `year_2023`, `year_2024`, `year_2025`, `year_2026`

### 5. **unified_data_DataType_Raghu** (Properties table)
- **Link**: Matches `locations.name` via `areaname` (fuzzy matching)
- **Purpose**: Real estate property listings
- **Columns**: `id`, `projectname`, `buildername`, `areaname`, `price_per_sft`, `baseprojectprice`, `bhk`, `sqfeet`, etc.

### 6. **location_costs**
- **Foreign Key**: `location_id` → `locations.id`
- **Purpose**: Property cost statistics per location
- **Columns**: `location_id`, cost-related fields

## Table Relationship Diagram

```
┌─────────────────┐
│   locations     │ (Master Table)
│  - id (PK)      │
│  - name         │
│  - geom         │
└────────┬────────┘
         │
         ├──────────────────────────────────────────┐
         │                                          │
         │ (location_id FK)                         │ (location_id FK)
         ▼                                          ▼
┌──────────────────────┐                  ┌──────────────────────┐
│ news_balanced_       │                  │ location_insights    │
│ corpus_1             │                  │  - location_id (FK)  │
│  - location_id (FK)  │                  │  - avg_sentiment     │
│  - location_name     │                  │  - growth_score      │
│  - sentiment_score   │                  │  - investment_score  │
└──────────────────────┘                  └──────────────────────┘
         
         │ (location_id FK)
         ▼
┌──────────────────────┐
│ location_costs       │
│  - location_id (FK)  │
│  - cost data         │
└──────────────────────┘

         │ (name matching)
         ▼
┌──────────────────────┐
│ price_trends         │
│  - location (name)   │
│  - year_2020-2026    │
└──────────────────────┘

         │ (areaname fuzzy matching)
         ▼
┌──────────────────────────────┐
│ unified_data_DataType_Raghu  │
│  - areaname (fuzzy match)    │
│  - projectname               │
│  - price_per_sft             │
│  - bhk, sqfeet, etc.         │
└──────────────────────────────┘
```

## Key Relationships

### Direct Foreign Key Relationships (location_id)
1. **locations** ← **news_balanced_corpus_1** (via `location_id`)
2. **locations** ← **location_insights** (via `location_id`)
3. **locations** ← **location_costs** (via `location_id`)

### Name-Based Relationships (fuzzy matching)
4. **locations.name** ← **price_trends.location** (exact name match, case-insensitive)
5. **locations.name** ← **unified_data_DataType_Raghu.areaname** (fuzzy match with multiple strategies)

## Fuzzy Matching Logic for Properties

The `unified_data_DataType_Raghu` table uses sophisticated fuzzy matching:

```sql
LOWER(areaname) = LOWER(location.name)
OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(location.name, ' ', ''))
OR areaname ILIKE location.name
OR location.name ILIKE areaname
```

This handles variations like:
- "HITEC City" vs "Hitec City"
- "Appa Junction" vs "AppaJunction"
- Case differences

## API Endpoints Using These Relationships

### `/api/v1/insights`
**Tables Used**: 
- `locations` (master)
- `location_insights` (LEFT JOIN on location_id)
- `news_balanced_corpus_1` (aggregated count)
- `unified_data_DataType_Raghu` (fuzzy matched on areaname)

### `/api/v1/location/{id}/trends`
**Tables Used**:
- `locations` (get name by id)
- `price_trends` (match by location name)

### `/api/v1/properties?area=X`
**Tables Used**:
- `unified_data_DataType_Raghu` (filter by areaname)

### `/api/v1/search`
**Tables Used**:
- `news_balanced_corpus_1` (search location_name)

## Important Notes

1. **All tables are in Supabase PostgreSQL** - they need direct database connection
2. **location_id is the primary linking field** for most relationships
3. **Name-based matching** is used for `price_trends` and `unified_data_DataType_Raghu`
4. **Fuzzy matching** is critical for property data due to inconsistent naming

## Tables NOT in Current Schema

These were removed during migration:
- ❌ `location_infrastructure` - Not available in new Supabase schema
- ❌ `properties_final` - Renamed to `unified_data_DataType_Raghu`
