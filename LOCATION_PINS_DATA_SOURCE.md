# Location Pins Data Source

## Overview

The location pins (dots) displayed on the map are loaded from a combination of multiple database tables through the `get_all_insights()` RPC function.

## Primary Tables

### 1. **`locations`** (Main table)
- **Purpose:** Core location data with coordinates
- **Key fields:**
  - `id` - Location ID
  - `name` - Location name (e.g., "Gachibowli", "Kondapur")
  - `geom` - Geometry data in POINT(longitude latitude) format
  - `city` - City name (Hyderabad or Bangalore)

### 2. **`location_insights`** (Hyderabad & Bangalore)
- **Purpose:** Calculated insights and scores for each location
- **Key fields:**
  - `location_id` - Links to locations.id
  - `avg_sentiment_score` - Average sentiment from news articles
  - `growth_score` - Infrastructure growth score
  - `investment_score` - Investment potential score
  - `connectivity_score` - Transportation connectivity
  - `amenities_score` - Nearby amenities score
  - `sentiment_summary` - Text summary of sentiment
  - `growth_summary` - Text summary of growth
  - `invest_summary` - Text summary of investment potential

**Note:** There are two separate tables:
- `hyderabad_locations` - Hyderabad location insights
- `bangalore_locations` - Bangalore location insights

### 3. **`unified_data_DataType_Raghu`** (Property data)
- **Purpose:** Property listings for price calculations
- **Key fields:**
  - `areaname` - Location/area name
  - `price_per_sft` - Price per square foot
  - Used to calculate: avg price, min price, max price, property count

### 4. **`news_balanced_corpus_1`** (News articles)
- **Purpose:** News articles about locations
- **Key fields:**
  - `location_id` - Links to locations.id
  - Used to calculate: article count

## Data Flow

```
get_all_insights() RPC Function
  ↓
Queries 4 tables:
  ├─ locations (coordinates, names)
  ├─ location_insights (scores, summaries)
  ├─ unified_data_DataType_Raghu (property prices)
  └─ news_balanced_corpus_1 (article counts)
  ↓
Returns combined data with:
  - Location coordinates (for map pins)
  - Sentiment scores
  - Growth & investment scores
  - Property statistics
  - Article counts
  - Text summaries
  ↓
Frontend (app.js)
  ↓
Creates GeoJSON features
  ↓
Adds to map as "locations" source
  ↓
Renders as pins on map
```

## RPC Function: `get_all_insights()`

**Location:** `supabase_functions.sql` (lines 49-150)

**Returns:**
```sql
RETURNS TABLE (
    location_id INT,
    location TEXT,
    longitude FLOAT,
    latitude FLOAT,
    avg_sentiment FLOAT,
    growth_score FLOAT,
    investment_score FLOAT,
    article_count INT,
    avg_property_price FLOAT,
    property_count INT,
    min_property_price FLOAT,
    max_property_price FLOAT,
    price_summary TEXT,
    sentiment_summary TEXT,
    growth_summary TEXT,
    invest_summary TEXT
)
```

## How It Works

### Step 1: Property Statistics
```sql
WITH property_stats AS (
    SELECT 
        LOWER(areaname) as area_lower,
        COUNT(*) as property_count,
        AVG(price_per_sft) as avg_price_per_sft,
        MIN(price_per_sft) as min_price_per_sft,
        MAX(price_per_sft) as max_price_per_sft
    FROM "unified_data_DataType_Raghu" 
    WHERE price_per_sft > 0
    GROUP BY LOWER(areaname), areaname
)
```

### Step 2: Match Locations to Properties
```sql
location_property_matches AS (
    SELECT 
        l.id as loc_id,
        l.name as loc_name,
        SUM(ps.property_count) as total_property_count,
        AVG(ps.avg_price_per_sft) as avg_price_per_sft
    FROM locations l
    LEFT JOIN property_stats ps ON (
        LOWER(TRIM(ps.original_area)) = LOWER(TRIM(l.name))
        OR LOWER(REPLACE(TRIM(ps.original_area), ' ', '')) = LOWER(REPLACE(TRIM(l.name), ' ', ''))
        OR TRIM(ps.original_area) ILIKE TRIM(l.name)
    )
    GROUP BY l.id, l.name
)
```

### Step 3: Article Statistics
```sql
article_stats AS (
    SELECT 
        location_id,
        COUNT(*) as article_count
    FROM news_balanced_corpus_1
    GROUP BY location_id
)
```

### Step 4: Combine All Data
```sql
SELECT
    l.id,
    l.name,
    -- Parse coordinates from POINT(x y) format
    CAST(SPLIT_PART(...) AS FLOAT) as longitude,
    CAST(SPLIT_PART(...) AS FLOAT) as latitude,
    COALESCE(li.avg_sentiment_score, 0),
    COALESCE(li.growth_score, 0),
    COALESCE(li.investment_score, 0),
    COALESCE(a.article_count, 0),
    COALESCE(lpm.avg_price_per_sft, 0),
    COALESCE(lpm.total_property_count, 0),
    -- ... etc
FROM locations l
LEFT JOIN location_insights li ON li.location_id = l.id
LEFT JOIN location_property_matches lpm ON lpm.loc_id = l.id
LEFT JOIN article_stats a ON a.art_loc_id = l.id
```

## Frontend Implementation

**File:** `frontend/app.js` (lines 95-98, 1411-1450)

### Data Fetching
```javascript
const insightsPromise = waitForSupabaseConfig().then(() => {
  return callSupabaseRPC('get_all_insights').then(data => {
    return data;
  });
});
```

### Map Source Creation
```javascript
map.addSource("locations", {
  type: "geojson",
  data: {
    type: "FeatureCollection",
    features: data.map(d => ({
      type: "Feature",
      geometry: { 
        type: "Point", 
        coordinates: [d.longitude, d.latitude] 
      },
      properties: d
    }))
  }
});
```

### Map Layers
```javascript
// Glow ring (background)
map.addLayer({
  id: "location-glow",
  type: "circle",
  source: "locations",
  paint: {
    "circle-radius": [8-12],
    "circle-color": "#3350C0",
    "circle-opacity": 0.1
  }
});

// Core dot (foreground)
map.addLayer({
  id: "location-core",
  type: "circle",
  source: "locations",
  paint: {
    "circle-radius": [3.5-5.5],
    "circle-color": "#1A1C1E",
    "circle-stroke-color": "#FFFFFF",
    "circle-stroke-width": 1.5
  }
});
```

## Pin Appearance

Each location pin consists of:
1. **Glow ring** - Blue (#3350C0) with 10% opacity, 8-12px radius
2. **Core dot** - Dark (#1A1C1E) with white stroke, 3.5-5.5px radius

## Data Updates

### When are pins updated?
- On initial page load
- When switching cities (Hyderabad ↔ Bangalore)
- When refreshing the page

### How to update pin data?
1. Update data in source tables:
   - `locations` - Add/update location coordinates
   - `location_insights` - Update scores and summaries
   - `unified_data_DataType_Raghu` - Add/update properties
   - `news_balanced_corpus_1` - Add/update news articles

2. The `get_all_insights()` function automatically combines the data

3. Frontend fetches fresh data on page load

## Related Tables

### Hyderabad-specific:
- `hyderabad_locations` - Location insights for Hyderabad

### Bangalore-specific:
- `bangalore_locations` - Location insights for Bangalore

### Shared:
- `locations` - All locations (both cities)
- `unified_data_DataType_Raghu` - All properties (both cities)
- `news_balanced_corpus_1` - All news articles (both cities)

## Summary

**Location pins are loaded from:**
1. **Primary:** `locations` table (coordinates, names)
2. **Insights:** `location_insights` / `hyderabad_locations` / `bangalore_locations` (scores)
3. **Properties:** `unified_data_DataType_Raghu` (price data)
4. **News:** `news_balanced_corpus_1` (article counts)

**Via:** `get_all_insights()` RPC function

**Displayed as:** Blue-glowing dots with dark cores on the map

**Total locations:** ~100-200 pins (varies by city)
