# Endpoints NOT Being Used Anywhere

## ❌ COMPLETELY UNUSED (3 endpoints)

### 1. GET /api/v1/market-trends
**Purpose**: Average price trend across ALL locations (Hyderabad baseline)  
**Returns**: Array of {year, price} from 2020-2026  
**Used by**: NOTHING  
**Can remove**: YES

### 2. GET /api/v1/property-costs (bulk - no parameter)
**Purpose**: Get property cost statistics for ALL locations  
**Returns**: Array of all locations with prices  
**Used by**: NOTHING  
**Can remove**: YES

### 3. GET /api/v1/location-costs (bulk - no parameter)
**Purpose**: Get location costs for ALL locations  
**Returns**: Array of all locations  
**Used by**: Test file only (utilities/test_all_endpoints.py)  
**Can remove**: Maybe (if you don't need test)

---

## 🧪 USED ONLY IN TEST FILES (3 endpoints)

### 4. GET /api/v1/location-costs/{name}
**Purpose**: Simple cost statistics for one location  
**Used by**: utilities/test_all_endpoints.py, utilities/test_api.py  
**Frontend uses**: NO (uses property-costs instead)  
**Can remove**: YES (if you remove test files or update them)

### 5. GET /api/v1/location/{id}/infra
**Purpose**: Infrastructure counts (hospitals, schools, etc.)  
**Used by**: utilities/test_all_endpoints.py  
**Frontend uses**: NO (uses amenities endpoint instead)  
**Problem**: References non-existent table, uses slow Overpass API  
**Can remove**: YES

### 6. GET /api/v1/location-costs (bulk)
**Purpose**: All location costs  
**Used by**: utilities/test_all_endpoints.py  
**Frontend uses**: NO  
**Can remove**: YES (if you remove test file)

---

## 🔧 UTILITY ENDPOINTS (Keep These)

### 7. GET /
**Purpose**: Health check  
**Used by**: Monitoring/deployment  
**Can remove**: NO - Keep for monitoring

### 8. GET /api/v1/search/debug
**Purpose**: Debug search functionality  
**Used by**: Manual debugging  
**Can remove**: NO - Keep for debugging

---

## 📊 SUMMARY

### Completely Unused (Safe to Remove) - 2 endpoints
1. /api/v1/market-trends
2. /api/v1/property-costs (bulk)

### Test-Only (Can Remove if Tests Updated) - 3 endpoints
3. /api/v1/location-costs (bulk)
4. /api/v1/location-costs/{name}
5. /api/v1/location/{id}/infra

### Utility (Keep) - 2 endpoints
6. / (health check)
7. /api/v1/search/debug

---

## 🎯 RECOMMENDATION

### Remove Immediately (2 endpoints):
```
❌ /api/v1/market-trends
❌ /api/v1/property-costs (bulk)
```

### Remove if You Don't Need Tests (3 endpoints):
```
❌ /api/v1/location-costs (bulk)
❌ /api/v1/location-costs/{name}
❌ /api/v1/location/{id}/infra
```

### Keep (12 endpoints):
```
✅ / (health)
✅ /api/v1/search/debug
✅ /api/v1/insights
✅ /api/v1/search
✅ /api/v1/properties
✅ /api/v1/properties/{id}
✅ /api/v1/location/{id}/trends
✅ /api/v1/property-costs/{name}
✅ /api/v1/location/{id}/amenities/{type}
```

---

## 💡 FINAL COUNT

**Current**: 20 endpoints  
**Remove completely unused**: -2 = 18 endpoints  
**Remove test-only**: -3 = 15 endpoints  
**Keep**: 12 endpoints (7 frontend + 2 utility + 3 test-only if you want)

**Want me to remove the 2 completely unused endpoints?**
