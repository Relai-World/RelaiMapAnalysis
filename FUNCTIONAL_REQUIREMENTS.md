# Real Estate Intelligence Platform
## Functional Requirements Document (FRD)

**Company:** Relai  
**Document Type:** Functional Requirements Specification  
**Version:** 1.0  
**Date:** February 15, 2026  
**Status:** Living Document  
**Prepared By:** Development Team  

---

## 1. Document Purpose & Scope

### 1.1 Purpose
This document defines the complete functional requirements for the **Real Estate Intelligence Platform** — a geospatial analytics system that harvests, processes, and visualizes micro-market intelligence for the Hyderabad real estate market. It serves as the authoritative reference for what the platform does, how users interact with it, and how each feature operates from both user-facing and system-level perspectives.

### 1.2 Scope
The platform covers:
- **~300 micro-market locations** across all of Hyderabad
- **Automated data harvesting** from news and community sources
- **AI-powered sentiment analysis** using FinBERT
- **Interactive geospatial visualization** with vector maps
- **Real-time price analytics** and trend comparisons
- **Automated refresh cycle** for continuous intelligence

### 1.3 Target Users

| User Type | Description | Primary Use |
|-----------|-------------|-------------|
| **Real Estate Analyst** | Market researcher studying investment zones | Compare locations, analyze price trends, identify hotspots |
| **Investor** | Individual or institutional buyer evaluating options | Quick location intelligence, property cost data, growth scores |
| **Corporate Decision Maker** | Executive needing market overview | High-level sentiment maps, city-wide trend dashboards |
| **Urban Planner** | Government or private sector planner | Infrastructure overlay analysis, boundary mapping |

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
│  Google News RSS │ Reddit │ Unified CSV │ Overpass (OSM)    │
└─────────┬────────┴────────┴──────┬──────┴────────┬──────────┘
          │                        │               │
          ▼                        ▼               ▼
┌─────────────────┐  ┌────────────────┐  ┌────────────────────┐
│  WEB SCRAPERS   │  │  ETL PIPELINE  │  │  LIVE OSM QUERIES  │
│  (Playwright)   │  │  (CSV Import)  │  │  (Overpass API)    │
└────────┬────────┘  └───────┬────────┘  └─────────┬──────────┘
         │                   │                     │
         ▼                   ▼                     │
┌─────────────────┐  ┌────────────────┐            │
│  FinBERT NLP    │  │  Aggregation   │            │
│  (Sentiment)    │──│  Engine        │            │
└────────┬────────┘  └───────┬────────┘            │
         │                   │                     │
         ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL + PostGIS DATABASE                   │
│  locations │ location_insights │ price_trends │ infra │ etc │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI BACKEND                           │
│   /insights │ /trends │ /amenities │ /costs │ /boundary     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                        │
│  MapLibre GL │ Intel Card │ Trends Page │ Search │ Layers   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Scraping** | Playwright (Async), BeautifulSoup, feedparser | Automated web data harvesting |
| **NLP / AI** | FinBERT (ProsusAI/finbert), HuggingFace Transformers | Financial sentiment analysis |
| **Database** | PostgreSQL 15 + PostGIS | Geospatial data storage & querying |
| **Backend API** | FastAPI + Uvicorn (ASGI) | High-performance REST API |
| **Frontend Map** | MapLibre GL JS + PMTiles | Vector-based interactive maps |
| **Charts** | Chart.js 4.x | Price trend visualization |
| **PDF Generation** | jsPDF | Client-side report export |
| **External APIs** | Overpass (OpenStreetMap) | Live amenity data (hospitals, schools, etc.) |

---

## 3. Functional Requirements — Data Acquisition Module

### FR-3.1: Google News Scraping

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-3.1 |
| **Priority** | Critical |
| **Component** | `scraper/scrape_playwright.py` |
| **Trigger** | Manual execution or scheduled automation |

**Description:**  
The system shall scrape real estate and infrastructure news from Google News RSS feeds using headless Chromium (Playwright). Articles are fetched using targeted search queries per location or city-wide inverted queries.

**Functional Behavior:**
1. System constructs search queries using location names + topic keywords (e.g., *"Gachibowli Hyderabad infrastructure OR metro"*)
2. Queries are restricted by configurable date ranges (default: last 3 years)
3. RSS feed is parsed using `feedparser` to extract article URLs, titles, and published dates
4. For each valid article URL:
   - Playwright renders the page using headless Chromium
   - Article text is extracted (with domain validation to skip paywalled/non-scraping sites)
   - Content is cleaned and validated for minimum length
5. Extracted articles are stored in the `news_balanced_corpus` database table with metadata:
   - `location_id`, `title`, `content`, `source_url`, `published_date`, `scraped_at`
6. Duplicate articles (by URL) are automatically skipped

**Error Handling:**
- Rate limiting with configurable delays (2-3 seconds between requests)
- Retry logic with exponential backoff on failures
- Graceful handling of blocked/403 responses

---

### FR-3.2: Reddit Community Scraping

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-3.2 |
| **Priority** | High |
| **Component** | `scraper/scrape_reddit_targeted.py` |

**Description:**  
The system shall scrape community sentiment data from Reddit communities (`r/hyderabad`, `r/IndiaRealEstate`) to capture unfiltered public opinion about specific locations.

**Functional Behavior:**
1. System executes targeted searches for high-intent keywords: *"review"*, *"water problem"*, *"traffic"*, *"cost of living"*, etc.
2. Both main post body and top comments are captured
3. Text is tagged to specific locations using keyword matching
4. Data is stored in the same sentiment processing pipeline as news data

---

### FR-3.3: CSV Data Import (Bulk ETL)

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-3.3 |
| **Priority** | Critical |
| **Component** | `utilities/import_csv_data.py` |

**Description:**  
The system shall import bulk location data from a unified CSV dataset (`unified_data_DataType_Raghu_rows.csv`) containing project-level metrics, Google Place Ratings, and infrastructure counts.

**Functional Behavior:**
1. **Normalization:**
   - Raw ratings (0-5) are mapped to a unified (-1.0 to 1.0) scale
   - Connectivity and GRID scores are parsed as floating-point values
2. **Aggregation (Project → Location):**
   - Individual real estate projects are grouped by `areaname` into micro-market locations
   - Infrastructure counts (hospitals, schools) are aggregated using MAX (development ceiling)
3. **Geospatial Persistence:**
   - Coordinates are stored as PostGIS `POINT` geometry using `ST_MakePoint` (SRID 4326)
   - Data is distributed across `locations`, `location_insights`, and `location_infrastructure` tables

---

## 4. Functional Requirements — NLP & Intelligence Processing

### FR-4.1: FinBERT Sentiment Analysis

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-4.1 |
| **Priority** | Critical |
| **Component** | `sentiment/main_sentiment.py` |
| **Model** | `ProsusAI/finbert` (HuggingFace) |

**Description:**  
The system shall analyze scraped text using FinBERT, a pre-trained NLP model optimized for financial and economic contexts, to derive quantitative sentiment scores for each location.

**Why FinBERT (vs. Generic Sentiment):**
- Understands financial nuance: *"Price surge"* = Positive for investors (generic models may see "surge" as negative)
- Pre-trained on financial text corpus — no fine-tuning required
- Zero-shot inference mode: model weights are frozen, not retrained

**Functional Behavior:**
1. **Input:** Raw text chunks from scraped articles or Reddit comments
2. **Tokenization:** Text is tokenized into BERT-compatible input format
3. **Inference:** FinBERT outputs probability distributions across 3 classes:
   - `Positive`, `Negative`, `Neutral`
   - *Example:* "Metro line approved for Nagole" → `Positive: 0.92`
4. **Score Storage:** Per-article sentiment scores are stored in `processed_sentiment_data` table linked to `location_id`

---

### FR-4.2: Score Aggregation (Moving Average)

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-4.2 |
| **Priority** | Critical |
| **Component** | `aggregation/compute_location_insights.py` |

**Description:**  
The system shall aggregate individual article sentiment scores into location-level metrics using a weighted moving average, ensuring gradual score evolution.

**Functional Behavior:**
1. **Per-Location Aggregation:** All sentiment scores for a given location are averaged
2. **Moving Average Formula (for incremental updates):**
   ```
   New_Avg = ((Old_Avg × Old_Count) + (New_Score × New_Count)) / Total_Count
   ```
3. **Derived Scores:** From raw sentiment, the system computes:
   - `avg_sentiment_score` (-1.0 to 1.0): Overall market sentiment
   - `growth_score` (0.0 to 1.0): Growth potential derived from sentiment + infrastructure
   - `investment_score` (0.0 to 1.0): Investment attractiveness combining all factors
4. **Result:** Updated `location_insights` table

**Design Rationale:**  
One negative article should not crash a location's score. Conversely, a consistent stream of negative news will gradually drag scores down. This mirrors how real markets respond to information.

---

### FR-4.3: Dynamic Smart Facts Generation

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-4.3 |
| **Priority** | High |
| **Component** | `aggregation/generate_smart_facts.py`, `api.py → fetch_dynamic_facts()` |

**Description:**  
The system shall generate human-readable, data-driven insights ("Smart Copy") for each location based on its scores and infrastructure profile.

**Functional Behavior:**
1. **Sentiment-Based Facts:**
   - Score ≥ 0.4 → *"🔥 Investor Favorite: High buzz driven by rapid commercial development."*
   - Score ≥ 0.1 → *"✅ Positive Outlook: Steady infrastructure upgrades boosting confidence."*
   - Score ≥ -0.1 → *"⚖️ Balanced Market: Stable demand with consistent long-term value."*
   - Score < -0.1 → *"👀 Value Pick: Market consolidation offers unique entry points."*

2. **Growth-Based Facts (Infrastructure-Driven):**
   - Metro access → *"🚇 Super Connected: Direct Metro access ensures unbeatable commute."*
   - Airport proximity → *"✈️ Global Gateway: Strategic proximity to International Airport."*
   - Schools > 5 → *"🏫 Family Prime: Surrounded by X+ top-tier international schools."*
   - Hospitals > 3 → *"🏥 Medical Hub: World-class healthcare access within minutes."*
   - Default → *"🏗️ Developing Fast: New roads and civic infra coming up."*

3. **Investment-Based Facts (CAGR-Driven):**
   - CAGR > 12% → *"🚀 Skyrocketing: Explosive annual growth track record."*
   - CAGR > 8% → *"💎 Wealth Builder: Strong consistent annual returns."*
   - Default → *"🛡️ Safe Bet: Steady appreciation beating inflation."*

---

## 5. Functional Requirements — Backend API

### FR-5.1: Core Insights API

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.1 |
| **Endpoint** | `GET /api/v1/insights` |
| **Response** | JSON Array |

**Description:**  
Returns comprehensive analytics data for ALL locations including coordinates, scores, article counts, and dynamically generated smart facts.

**Response Schema (per location):**
```json
{
  "location_id": 42,
  "location": "LB Nagar",
  "longitude": 78.552,
  "latitude": 17.347,
  "avg_sentiment": 0.35,
  "growth_score": 0.72,
  "investment_score": 0.65,
  "article_count": 23,
  "sentiment_summary": "🔥 Investor Favorite: High buzz...",
  "growth_summary": "🚇 Super Connected: Direct Metro...",
  "invest_summary": "💎 Wealth Builder: Strong consistent..."
}
```

**Usage:** Powers the map markers, search autocomplete, Intel Card data, and PDF report generation.

---

### FR-5.2: Location Infrastructure API

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.2 |
| **Endpoint** | `GET /api/v1/location/{location_id}/infra` |
| **Data Source** | Live Overpass (OpenStreetMap) API |

**Description:**  
Returns real-time infrastructure counts within a 5km radius of a given location by querying the OpenStreetMap Overpass API.

**Response Schema:**
```json
{
  "hospitals": 12,
  "schools": 8,
  "metro": 2,
  "airports": 0,
  "malls": 3
}
```

---

### FR-5.3: Price Trends API

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.3a |
| **Endpoint** | `GET /api/v1/location/{location_id}/trends` |

**Description:**  
Returns annual average price per square foot for a specific location (2023–2026).

**Response Schema:**
```json
[
  {"year": 2023, "price": 5200.0},
  {"year": 2024, "price": 5800.0},
  {"year": 2025, "price": 6500.0},
  {"year": 2026, "price": 7100.0}
]
```

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.3b |
| **Endpoint** | `GET /api/v1/market-trends` |

**Description:**  
Returns the Hyderabad city-wide average price trend (baseline for comparison across all locations).

---

### FR-5.4: Location Costs API

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.4a |
| **Endpoint** | `GET /api/v1/location-costs` |

**Description:**  
Returns property cost statistics (average base price in Crores, average price/sqft, min/max ranges) for ALL locations. Used for city-wide comparisons.

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.4b |
| **Endpoint** | `GET /api/v1/location-costs/{location_name}` |

**Description:**  
Returns property cost statistics for a specific location by name (case-insensitive match).

**Response Schema:**
```json
{
  "location": "Gachibowli",
  "count": 34,
  "avgBase": 1.25,
  "avgSqft": 8500,
  "minBase": 0.65,
  "maxBase": 2.80,
  "minSqft": 5200,
  "maxSqft": 14000
}
```

---

### FR-5.5: Nearby Amenities API

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.5 |
| **Endpoint** | `GET /api/v1/location/{location_id}/amenities/{amenity_type}` |
| **Data Source** | Live Overpass (OpenStreetMap) API |
| **Amenity Types** | `hospitals`, `schools`, `malls`, `restaurants`, `banks`, `atms`, `parks`, `gyms`, `cafes`, `metro`, `metro_stations`, `pharmacies`, `supermarkets` |

**Description:**  
Returns detailed amenity locations with geographic coordinates for map plotting. Amenities are fetched within a 5km radius of the selected location, with distance-based color coding.

**Response Schema:**
```json
{
  "location": "Gachibowli",
  "location_lat": 17.4401,
  "location_lng": 78.3489,
  "amenity_type": "hospitals",
  "total_count": 15,
  "amenities": [
    {
      "name": "Apollo Hospital",
      "latitude": 17.442,
      "longitude": 78.351,
      "distance_km": 1.2,
      "color": "green",
      "osm_id": 12345678
    }
  ],
  "color_legend": {
    "green": "0-2 km (Close)",
    "orange": "2-3.5 km (Medium)",
    "red": "3.5-5 km (Far)"
  }
}
```

---

### FR-5.6: Location Boundary API

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-5.6 |
| **Endpoint** | `GET /api/v1/location/{location_id}/boundary` |

**Description:**  
Returns the GeoJSON boundary geometry for a specific location (if available), used for highlighting the selected area on the map.

---

## 6. Functional Requirements — Frontend: Interactive Map

### FR-6.1: Vector Map Engine

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.1 |
| **Component** | `frontend/index.html`, `frontend/app.js` |
| **Library** | MapLibre GL JS 3.6.2 |
| **Tile Format** | PMTiles (serverless vector tiles) |

**Description:**  
The system shall render an interactive, dark-themed vector map centered on Hyderabad, supporting smooth zooming, panning, and 3D pitch controls.

**Functional Behavior:**
1. Map initializes with a custom dark mode style (`style.json`)
2. PMTiles are pre-fetched (warm-up) at load time for snappy layer toggling
3. All ~300 location markers are rendered as `circle` layers from GeoJSON
4. Map supports zoom ranges from city-level overview to street-level detail

---

### FR-6.2: Location Markers & Color Coding

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.2 |

**Description:**  
Each location is displayed as a color-coded circle marker on the map. Marker color reflects the location's investment score or category.

**Marker Specification:**
- Circle radius: 6px
- Fill color: `#2735d1` (royal blue)
- Stroke: 2px white border
- Interactive: Click to open Intel Card

---

### FR-6.3: Intel Card (Location Detail Sidebar)

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.3 |
| **Component** | `#intel-card` in `index.html`, `handleLocationSelect()` in `app.js` |
| **Trigger** | Click on location marker OR select from search |

**Description:**  
When a user selects a location (via map click or search), a reactive sidebar ("Intel Card") slides in showing comprehensive location intelligence.

**Intel Card Sections:**

| Section | Data Source | Content |
|---------|-----------|---------|
| **Location Image** | Static assets (`assets/locations/`) | Hero image of the area (with default fallback) |
| **Title & Rating** | API `/insights` | Location name + investment score (★ X.X) + Location ID |
| **Market Sentiment** | Backend Smart Facts | Sentiment percentage, label, and AI-generated insight text |
| **Growth Potential** | Backend Smart Facts | Growth score (X.X/10) + infrastructure-based insight |
| **Investment Score** | Backend Smart Facts | Investment score (X.X/10) + CAGR-based insight |
| **Property Costs** | API `/location-costs/{name}` | Average base price (₹ Crores), Avg price/sqft, Min-Max ranges |
| **Nearby Amenities** | API `/amenities/{type}` | 7 amenity buttons (Hospitals, Schools, Malls, Restaurants, Banks, Parks, Metro) with distance color coding |
| **Price Trend Chart** | API `/location/{id}/trends` | Line chart (Chart.js) showing price/sqft 2023–2026 with CAGR stat |
| **Download Report** | Client-side (jsPDF) | Generates a professional PDF report |

**User Interaction Flow:**
1. User clicks a location marker on map
2. Map animates (`easeTo`) to the selected location at zoom level 13
3. Intel Card populates with all data sections
4. Property costs and price chart are fetched asynchronously (loading states shown)
5. Previous amenity markers are cleaned up before showing new location

---

### FR-6.4: Amenity Map Overlay

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.4 |
| **Trigger** | Click on amenity button in Intel Card |

**Description:**  
When a user clicks an amenity button (e.g., "🏥 Hospitals"), the system fetches nearby amenities via Overpass API and plots them as color-coded markers on the map.

**Functional Behavior:**
1. User clicks amenity button → Button shows loading state (`⏳ Loading...`)
2. System fetches amenities within 5km via `GET /api/v1/location/{id}/amenities/{type}`
3. Amenities are rendered as circle markers on the map with distance-based colors:
   - 🟢 Green: 0–2 km (Close)
   - 🟠 Orange: 2–3.5 km (Medium)
   - 🔴 Red: 3.5–5 km (Far)
4. A detailed amenity list card shows the name and distance for each amenity
5. Clicking a different amenity type replaces the previous markers
6. A "Clear" button removes all amenity markers

---

### FR-6.5: Global Search (Autocomplete)

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.5 |
| **Component** | `#location-search` input |
| **Behavior** | Starts-with matching, top 8 suggestions |

**Description:**  
The system shall provide a search input with real-time autocomplete across all ~300 locations. Users can find and navigate to any location by typing its name.

**Functional Behavior:**
1. User begins typing → Dropdown shows up to 8 matching locations (sorted alphabetically)
2. Matching algorithm: **starts-with** (case-insensitive)
3. Selecting a result (click or Enter) → Same behavior as map click:
   - Map flies to location
   - Intel Card opens with full data
4. If no match → *"No result found"* message displayed
5. Dropdown dismisses on click-outside or Escape

---

### FR-6.6: Map Layer Controls

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.6 |
| **Component** | `#layers-card` |

**Description:**  
The system shall provide toggleable map layers for geographic and infrastructure overlays, using a visual tile-grid UI.

**Available Layers:**

| Layer | Source | Format | Visual |
|-------|--------|--------|--------|
| **Highways** | OSM Data | PMTiles (Vector) | Purple lines |
| **Metro Lines** | OSM Data | PMTiles (Vector) | Red lines |
| **Outer Ring Road (ORR)** | OSM Data | PMTiles (Vector) | Black lines |
| **Lakes** | OSM Data | PMTiles (Vector) | Blue fill |
| **Regional Ring Road (RRR)** | Custom GeoJSON | GeoJSON | Dark orange lines |
| **HMDA Boundary** | Custom GeoJSON | GeoJSON | Royal blue dashed lines |
| **Mandals** | OSM Boundaries | GeoJSON | Blue lines (zoom 8+) |
| **Villages** | OSM Boundaries | GeoJSON | Green lines (zoom 13+) |

**Ghost Loading Pattern:**
- All layers are loaded at startup with `opacity: 0` (invisible)
- Toggling a layer checkbox smoothly fades the layer in/out
- This ensures instant visual response with no loading delays

---

### FR-6.7: PDF Report Generation

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-6.7 |
| **Component** | `generateReport()` in `app.js` |
| **Library** | jsPDF 2.5.1 |

**Description:**  
The system shall generate a downloadable PDF report for any selected location containing all analytics data from the Intel Card.

**PDF Content:**
1. **Header:** "REAL ESTATE INTELLIGENCE REPORT" + Location Name
2. **Scores Section:** Sentiment, Growth, Investment scores with labels
3. **Quick Facts:** AI-generated smart facts (3 insights)
4. **Property Costs:** Average base price, avg price/sqft, price ranges
5. **Nearby Amenities:** List of selected amenity type with distances (up to 10)
6. **Footer:** Source attribution and disclaimer

**File Name:** `{LocationName}_Detailed_Report.pdf`

---

## 7. Functional Requirements — Frontend: Price Trends Page

### FR-7.1: Price Trends Dashboard

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-7.1 |
| **Component** | `frontend/trends.html`, `frontend/trends.js` |
| **Library** | Chart.js 4.4.0 |

**Description:**  
A dedicated page for visualizing and comparing price trends across multiple locations with the Hyderabad city-wide baseline.

**Page Layout:**
1. **Header:** Back-to-map link + page title
2. **Location Selector:** Dropdown of all ~300 locations
3. **Selected Location Pills:** Visual chips showing selected locations with remove buttons
4. **Interactive Chart:** Line chart with quarterly price data (Q1'21 – Q3'25)
5. **Statistics Table:** Current quarter price range, average, and location count
6. **Source Attribution:** Data source citation

**Functional Behavior:**
1. Page loads → Hyderabad baseline (dashed gray line) is shown by default
2. User selects a location from dropdown → New colored line is added to chart
3. Maximum 5 locations can be compared simultaneously (+ Hyderabad baseline)
4. Each location gets a unique color from a curated palette
5. Pills are removable; removing a pill updates the chart instantly
6. Tooltip shows exact price per sqft on hover
7. Statistics table updates dynamically based on selected locations

**Hyderabad Baseline Data (2023–2026):**

| Year | Avg Price/sqft |
|------|----------------|
| 2023 | ₹6,447 |
| 2024 | ₹7,092 |
| 2025 | ₹7,730 |
| 2026 | ₹8,348 |

---

## 8. Functional Requirements — Data Pipeline & Automation

### FR-8.1: Update Pipeline (End-to-End Orchestrator)

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-8.1 |
| **Component** | `update_pipeline.py` |
| **Trigger** | Manual execution or scheduled automation |

**Description:**  
The system shall provide a single-command orchestrator that executes the entire intelligence refresh cycle in sequence.

**Pipeline Steps:**
```
Step 1: SCRAPING NEWS      → scraper/scrape_playwright.py
Step 2: SCRAPING REDDIT    → scraper/scrape_reddit_targeted.py
Step 3: PROCESSING SENTIMENT → sentiment/main_sentiment.py
Step 4: AGGREGATING INSIGHTS → aggregation/compute_location_insights.py
Step 5: GENERATE AI SUMMARIES → aggregation/generate_smart_facts.py
```

**Features:**
- `--skip-scrape` flag to run only processing steps (useful for testing)
- Each step reports success/failure with timing information
- Pipeline stops on critical failures (sentiment, aggregation) but continues on non-critical ones (fact generation)

---

### FR-8.2: Continuous Intelligence Loop

| Attribute | Detail |
|-----------|--------|
| **ID** | FR-8.2 |
| **Priority** | High |

**Description:**  
The system shall automatically refresh intelligence data on a configurable schedule (default: bi-weekly) using the 3-step continuous loop:

**The Loop:**

| Step | Name | What It Does |
|------|------|-------------|
| **1. LISTENING** | Data Harvesting | Scrapers wake up and fetch only NEW articles (incremental scan) |
| **2. THINKING** | Intelligence Processing | FinBERT scores new articles; moving average updates location scores |
| **3. PUBLISHING** | Visual Feedback | Database is updated; map colors, smart copy, and charts reflect new reality |

**Automation Requirements:**
- Scheduled via Windows Task Scheduler or cloud-based cron
- Incremental scanning: only fetch articles newer than `last_scraped` timestamp
- Error notification system (email/log alert on failure)
- Logging of each run with success/failure status

---

## 9. Database Schema

### 9.1 Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `locations` | Master location registry | `id`, `name`, `geom` (PostGIS Point), `boundary` (PostGIS Polygon) |
| `location_insights` | Aggregated intelligence scores | `location_id`, `avg_sentiment_score`, `growth_score`, `investment_score` |
| `location_infrastructure` | Infrastructure profile | `location_id`, `hospitals`, `schools`, `metro`, `airports` |
| `price_trends` | Historical price data | `location_id`, `year`, `avg_price_sqft` |
| `location_costs` | Property cost statistics | `location_name`, `property_count`, `avg_base_price`, `avg_price_sqft`, `min_base_price`, `max_base_price` |
| `news_balanced_corpus` | Raw scraped articles | `location_id`, `title`, `content`, `source_url`, `published_date` |
| `processed_sentiment_data` | Per-article FinBERT scores | `location_id`, `text`, `sentiment_label`, `sentiment_score` |

### 9.2 Spatial Data
- All coordinates stored as PostGIS `POINT` geometry (SRID 4326 / WGS84)
- Boundaries stored as PostGIS `POLYGON` or `MULTIPOLYGON`
- Spatial queries use PostGIS functions: `ST_MakePoint`, `ST_AsGeoJSON`, `ST_X`, `ST_Y`

---

## 10. Non-Functional Requirements

### NFR-10.1: Performance

| Metric | Target |
|--------|--------|
| API response time (p95) | < 500ms |
| Map initial load time | < 3 seconds |
| Search autocomplete response | < 100ms (client-side filtering) |
| Number of concurrent users | ≥ 50 (with connection pooling) |

### NFR-10.2: Scalability

| Metric | Target |
|--------|--------|
| Maximum locations | 500+ |
| Articles processed per refresh cycle | 500–2,000 |
| Database size (projected 1 year) | < 5 GB |

### NFR-10.3: Reliability

| Metric | Target |
|--------|--------|
| System uptime | > 99% |
| Data freshness | Scores updated within 14 days |
| Graceful degradation | Frontend functional even if individual API calls fail |

### NFR-10.4: Security

| Requirement | Implementation |
|-------------|---------------|
| Database access | Environment variables for credentials; SSL for remote connections |
| API access | CORS configured; rate limiting (planned) |
| No user PII stored | Platform is public-facing data only |

### NFR-10.5: Compatibility

| Browser | Version |
|---------|---------|
| Google Chrome | 100+ |
| Mozilla Firefox | 100+ |
| Microsoft Edge | 100+ |
| Safari | 15+ |
| Mobile browsers | Responsive design (pending) |

---

## 11. Feature Summary Matrix

| # | Feature | Module | Status | Priority |
|---|---------|--------|--------|----------|
| 1 | Interactive Vector Map (Dark Theme) | Frontend | ✅ Built | Critical |
| 2 | ~300 Location Markers | Frontend + API | ✅ Built | Critical |
| 3 | Intel Card (Location Detail Sidebar) | Frontend + API | ✅ Built | Critical |
| 4 | Global Search with Autocomplete | Frontend | ✅ Built | High |
| 5 | Map Layer Controls (7 layers) | Frontend | ✅ Built | High |
| 6 | News Scraping (Playwright) | Scraper | ✅ Built (7 Locations) | Critical |
| 7 | Reddit Scraping | Scraper | ✅ Built (7 Locations) | High |
| 8 | FinBERT Sentiment Analysis | NLP | ✅ Built (7 Locations) | Critical |
| 9 | Score Aggregation (Moving Average) | Aggregation | ✅ Built | Critical |
| 10 | Dynamic Smart Facts Generation | API + Aggregation | ✅ Built | High |
| 11 | Property Cost Display | Frontend + API | ✅ Built | High |
| 12 | Nearby Amenities (Overpass/OSM) | Frontend + API | ✅ Built | High |
| 13 | Price Trend Charts (Intel Card) | Frontend + API | ✅ Built | High |
| 14 | Price Trends Page (Multi-Compare) | Frontend | ✅ Built | Medium |
| 15 | PDF Report Download | Frontend (jsPDF) | ✅ Built | Medium |
| 16 | Update Pipeline Orchestrator | Pipeline | ✅ Built | Critical |
| 17 | CSV Bulk Import (ETL) | Utility | ✅ Built | Critical |
| 18 | City-Wide Inverted Scraping + NER | Scraper | ⏳ Planned | Critical |
| 19 | FinBERT at Scale (~300 locations) | NLP | ⏳ Planned | Critical |
| 20 | Automated Bi-Weekly Refresh | Automation | ⏳ Planned | High |
| 21 | Mobile Responsive Design | Frontend | ⏳ Planned | Medium |
| 22 | Production Cloud Deployment | DevOps | ⏳ Planned | High |
| 23 | Location Comparison API | API | ⏳ Planned | Medium |
| 24 | Trending Detection (Rapid Changes) | API + Aggregation | ⏳ Planned | Medium |

---

## 12. Glossary

| Term | Definition |
|------|-----------|
| **FinBERT** | A pre-trained NLP model based on BERT architecture, optimized for financial text analysis |
| **PostGIS** | A spatial database extension for PostgreSQL enabling geographic object storage and queries |
| **PMTiles** | A cloud-native format for storing and serving vector map tiles without a tile server |
| **MapLibre GL JS** | An open-source JavaScript library for rendering interactive vector maps in the browser |
| **Intel Card** | The platform's sidebar panel that displays detailed analytics for a selected location |
| **Smart Copy** | AI-generated, human-readable insight text derived from quantitative scores |
| **Moving Average** | A statistical method that blends new scores with historical averages for gradual updates |
| **CAGR** | Compound Annual Growth Rate — the annualized return over a given time period |
| **NER** | Named Entity Recognition — identifying location names within unstructured text |
| **SRID 4326** | The spatial reference system for GPS coordinates (WGS84 latitude/longitude) |
| **Overpass API** | A read-only API for querying OpenStreetMap data (amenities, roads, etc.) |
| **Ghost Loading** | A UX pattern where layers are pre-loaded invisibly and faded in on toggle |
| **Inverted Scraping** | A scaling strategy: scrape city-wide topics, then tag articles to locations via NER |

---

*This is a living document and will be updated as features are developed, tested, and deployed.*  
*Last Updated: February 15, 2026*
