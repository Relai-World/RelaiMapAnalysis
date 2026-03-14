# API Endpoints Analysis: Used vs Unused

## Summary
- **Total Endpoints Defined**: 31
- **Endpoints Used by Frontend**: 7
- **Unused Endpoints**: 24

---

## ✅ ENDPOINTS ACTIVELY USED BY FRONTEND

### 1. `/api/v1/insights` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Main data fetch on page load (line 80)
- **Purpose**: Fetches all location insights with sentiment, growth, and investment scores
- **Critical**: YES - Core feature

### 2. `/api/v1/search` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Search autocomplete (lines 609, 661)
- **Purpose**: Searches locations in news_balanced_corpus_1 table
- **Critical**: YES - Core search functionality

### 3. `/api/v1/properties` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Load properties by area (line 1179)
- **Query Params**: `?area={locationName}&bhk={optional}`
- **Purpose**: Fetches all properties for a specific location
- **Critical**: YES - Properties panel feature

### 4. `/api/v1/properties/{id}` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Property detail view (lines 1377, 1614, 2885)
- **Purpose**: Fetches single property full details
- **Critical**: YES - Property detail drawer

### 5. `/api/v1/location/{id}/trends` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Price chart rendering (line 1884)
- **Purpose**: Fetches price trends data for chart
- **Critical**: YES - Price trend visualization

### 6. `/api/v1/property-costs/{name}` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Property costs section (line 2112)
- **Purpose**: Fetches avg/min/max property costs for location
- **Critical**: YES - Cost statistics display

### 7. `/api/v1/location/{id}/amenities/{type}` (GET)
- **Status**: ✅ USED
- **Frontend Usage**: Amenity buttons (line 2223)
- **Purpose**: Fetches nearby amenities (hospitals, schools, etc.)
- **Critical**: YES - Amenities feature

---

## ❌ UNUSED ENDPOINTS (24 Total)

### General Endpoints

#### `/` (GET) - Health Check
- **Status**: ❌ UNUSED
- **Purpose**: API health check
- **Recommendation**: KEEP - Useful for monitoring

#### `/api/v1/search/debug` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Debug search functionality
- **Recommendation**: REMOVE - Debug endpoint not needed in production

### Location Infrastructure

#### `/api/v1/location/{id}/infrastructure` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Fetches infrastructure data (schools, hospitals, etc.)
- **Note**: References `location_infrastructure` table which doesn't exist
- **Recommendation**: REMOVE - Table doesn't exist, replaced by amenities endpoint

### Market Trends

#### `/api/v1/market-trends` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Aggregate market trends across all locations
- **Recommendation**: EVALUATE - Could be useful for future dashboard

### Property Costs (Bulk)

#### `/api/v1/location-costs` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: All location costs from location_costs table
- **Recommendation**: EVALUATE - Could be useful for comparison features

#### `/api/v1/property-costs` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: All property costs aggregated from unified_data
- **Recommendation**: EVALUATE - Could be useful for market overview

#### `/api/v1/property-costs/{area_name}` (GET)
- **Status**: ❌ UNUSED (Duplicate of used endpoint)
- **Purpose**: Same as `/api/v1/property-costs/{name}`
- **Recommendation**: REMOVE - Duplicate endpoint

### Telangana Registration Data (11 Endpoints)

#### `/api/v1/telangana/districts` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: List all Telangana districts
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/districts/{district_code}/mandals` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: List mandals in a district
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/mandals/{district_code}/{mandal_code}/villages` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: List villages in a mandal
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/market-values` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Registration market values with filters
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/top-locations` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Top locations by registration count
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/price-stats` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Price statistics from registration data
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/search` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Search Telangana locations
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/stats` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Overall Telangana statistics
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/telangana/villages/{village_id}/boundary` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Village boundary GeoJSON
- **Recommendation**: KEEP IF - Planning registration data feature

#### `/api/v1/location/{id}/boundary` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: Location boundary from database
- **Note**: Frontend uses Nominatim API directly instead
- **Recommendation**: REMOVE - Not used, frontend has alternative

#### `/api/v1/boundaries` (GET)
- **Status**: ❌ UNUSED
- **Purpose**: All location boundaries
- **Recommendation**: REMOVE - Not used

---

## 📊 RECOMMENDATIONS BY PRIORITY

### 🔴 HIGH PRIORITY: Remove Immediately

1. **`/api/v1/search/debug`** - Debug endpoint
2. **`/api/v1/location/{id}/infrastructure`** - References non-existent table
3. **`/api/v1/property-costs/{area_name}`** - Duplicate endpoint
4. **`/api/v1/location/{id}/boundary`** - Replaced by Nominatim
5. **`/api/v1/boundaries`** - Not used

### 🟡 MEDIUM PRIORITY: Evaluate for Future Use

1. **`/api/v1/market-trends`** - Could be useful for market overview page
2. **`/api/v1/location-costs`** - Could be useful for comparison features
3. **`/api/v1/property-costs`** - Could be useful for market dashboard

### 🟢 LOW PRIORITY: Keep for Future Features

**Telangana Registration Data Endpoints (11 total)**
- Keep if you plan to add registration data visualization
- Remove if this feature is not in roadmap
- These form a complete feature set for government registration data

### ✅ KEEP AS-IS

1. **`/` (health check)** - Useful for monitoring
2. **All 7 actively used endpoints** - Core functionality

---

## 🎯 CLEANUP IMPACT

### If you remove all unused endpoints:
- **Code reduction**: ~500-700 lines
- **Maintenance**: Reduced complexity
- **Performance**: Minimal impact (unused endpoints don't affect performance)
- **Risk**: Low (not used by frontend)

### If you keep Telangana endpoints:
- **Future-proofing**: Ready for registration data feature
- **Code size**: +300 lines
- **Decision point**: Do you plan to use government registration data?

---

## 📝 NEXT STEPS

1. **Confirm**: Do you want to keep Telangana registration endpoints?
2. **Remove**: Debug and duplicate endpoints immediately
3. **Document**: Mark "evaluate" endpoints for future consideration
4. **Test**: Verify frontend works after cleanup
5. **Deploy**: Push cleaned API to production

---

## 🔍 DETAILED ENDPOINT INVENTORY

### Used Endpoints (7)
```
GET  /api/v1/insights                          → insights()
GET  /api/v1/search                            → search_locations()
GET  /api/v1/properties                        → get_properties_by_area()
GET  /api/v1/properties/{id}                   → get_property_detail()
GET  /api/v1/location/{id}/trends              → get_location_trends()
GET  /api/v1/property-costs/{name}             → get_location_cost()
GET  /api/v1/location/{id}/amenities/{type}    → get_amenity_locations()
```

### Unused Endpoints (24)
```
GET  /                                         → health_check()
GET  /api/v1/search/debug                      → search_debug()
GET  /api/v1/location/{id}/infrastructure      → location_infra()
GET  /api/v1/market-trends                     → get_market_trends()
GET  /api/v1/location-costs                    → get_all_location_costs()
GET  /api/v1/property-costs                    → get_all_property_costs()
GET  /api/v1/property-costs/{area_name}        → get_area_property_costs()
GET  /api/v1/telangana/districts               → get_telangana_districts()
GET  /api/v1/telangana/districts/{dc}/mandals  → get_district_mandals()
GET  /api/v1/telangana/mandals/{dc}/{mc}/villages → get_mandal_villages()
GET  /api/v1/telangana/market-values           → get_telangana_market_values()
GET  /api/v1/telangana/top-locations           → get_telangana_top_locations()
GET  /api/v1/telangana/price-stats             → get_telangana_price_stats()
GET  /api/v1/telangana/search                  → search_telangana_locations()
GET  /api/v1/telangana/stats                   → get_telangana_overall_stats()
GET  /api/v1/telangana/villages/{id}/boundary  → get_telangana_village_boundary()
GET  /api/v1/location/{id}/boundary            → get_location_boundary()
GET  /api/v1/boundaries                        → get_all_boundaries()
```

---

**Generated**: March 13, 2026
**Analysis Scope**: api.py + frontend/app.js
