# Complete Endpoint Usage Analysis - All Files

## 🔍 FRONTEND (frontend/app.js) - 8 ENDPOINTS USED

1. ✅ **GET /api/v1/insights** (line 80)
   - Used on page load
   - Fetches all locations for map

2. ✅ **GET /api/v1/search** (lines 609, 661)
   - Search box autocomplete
   - Called twice (input event + enter key)

3. ✅ **GET /api/v1/properties** (line 1179)
   - Properties panel by area
   - Query params: ?area={name}&bhk={optional}

4. ✅ **GET /api/v1/properties/{id}** (lines 1377, 1614, 2885)
   - Property detail drawer
   - Called 3 times in different contexts

5. ✅ **GET /api/v1/location/{id}/trends** (line 1884)
   - Price chart rendering

6. ✅ **GET /api/v1/property-costs/{name}** (line 2112)
   - Property costs section in location card
   - Shows avg/min/max prices

7. ✅ **GET /api/v1/location/{id}/amenities/{type}** (line 2223)
   - Amenity buttons (hospitals, schools, etc.)

---

## 🧪 TEST FILES - 4 ENDPOINTS TESTED

### test_bhk_filter.py
- ✅ **GET /api/v1/properties** (lines 14, 33, 49)
  - Tests BHK filtering
  - Already counted above

### test_api_security.py
- ✅ **GET /api/v1/insights** (lines 16, 28, 43)
  - Tests API key security
  - Already counted above

### test_api_direct.py
- ✅ **GET /api/v1/properties** (line 14)
  - Direct API test
  - Already counted above

### utilities/test_all_endpoints.py
- ✅ **GET /api/v1/insights** (line 22)
- ✅ **GET /api/v1/location/{id}/trends** (line 37)
- ✅ **GET /api/v1/location-costs** (line 49) ⚠️ **NEW!**
- ✅ **GET /api/v1/location-costs/{name}** (line 64) ⚠️ **NEW!**
- ✅ **GET /api/v1/location/{id}/infra** (line 73) ⚠️ **NEW!**

### utilities/test_api.py
- ✅ **GET /api/v1/location-costs/{name}** (line 4)
  - Already counted above

### test_trends_api.py
- ✅ **GET /api/v1/location/{id}/trends** (line 44)
  - Already counted above

### test_property_detail.html
- ✅ **GET /api/v1/properties** (line 23)
  - Already counted above

---

## 📊 COMPLETE USAGE SUMMARY

### USED BY FRONTEND (Production) - 7 endpoints
1. /api/v1/insights
2. /api/v1/search
3. /api/v1/properties
4. /api/v1/properties/{id}
5. /api/v1/location/{id}/trends
6. /api/v1/property-costs/{name}
7. /api/v1/location/{id}/amenities/{type}

### USED BY TEST FILES ONLY - 3 endpoints
8. /api/v1/location-costs (bulk data)
9. /api/v1/location-costs/{name} (specific location)
10. /api/v1/location/{id}/infra (infrastructure counts)

### NEVER USED ANYWHERE - 10 endpoints
11. / (health check) - Not called but useful
12. /api/v1/search/debug - Debug only
13. /api/v1/market-trends - Market overview
14. /api/v1/property-costs (bulk) - Not called
15. /api/v1/property-costs/{area_name} - Detailed costs (DUPLICATE?)

---

## ⚠️ IMPORTANT FINDINGS

### 1. DUPLICATE ENDPOINTS?

**Frontend uses:**
```
/api/v1/property-costs/{name}  (line 2112 in app.js)
```

**Test file uses:**
```
/api/v1/location-costs/{name}  (utilities/test_all_endpoints.py)
```

**Question**: Are these the same or different?
- `/api/v1/property-costs/{name}` - Used by frontend
- `/api/v1/location-costs/{name}` - Used by test file

Need to check if they return the same data!

### 2. TEST-ONLY ENDPOINTS

These are ONLY used in test files, not production:
- `/api/v1/location-costs` (bulk)
- `/api/v1/location-costs/{name}` (specific)
- `/api/v1/location/{id}/infra` (infrastructure)

**Decision needed**: Keep for testing or remove?

---

## 🎯 CORRECTED ENDPOINT STATUS

### ✅ KEEP (Production Use) - 7 endpoints
1. /api/v1/insights
2. /api/v1/search
3. /api/v1/properties
4. /api/v1/properties/{id}
5. /api/v1/location/{id}/trends
6. /api/v1/property-costs/{name}
7. /api/v1/location/{id}/amenities/{type}

### 🧪 KEEP (Test Use) - 3 endpoints
8. /api/v1/location-costs
9. /api/v1/location-costs/{name}
10. /api/v1/location/{id}/infra

### 🔧 UTILITY - 2 endpoints
11. / (health check)
12. /api/v1/search/debug

### ❌ REMOVE - 8 endpoints
13. /api/v1/market-trends
14. /api/v1/property-costs (bulk)
15. /api/v1/property-costs/{area_name} (if duplicate)
16-24. All Telangana endpoints (ALREADY REMOVED)

---

## 🤔 QUESTIONS TO RESOLVE

1. **Is `/api/v1/property-costs/{name}` the same as `/api/v1/location-costs/{name}`?**
   - Frontend uses property-costs
   - Test uses location-costs
   - Are they duplicates?

2. **Should we keep test-only endpoints?**
   - `/api/v1/location-costs`
   - `/api/v1/location-costs/{name}`
   - `/api/v1/location/{id}/infra`

3. **What about `/api/v1/property-costs/{area_name}`?**
   - Is this different from property-costs/{name}?
   - Or is it a duplicate?

---

## 📝 NEXT STEPS

1. Check if property-costs and location-costs endpoints are duplicates
2. Decide on test-only endpoints
3. Remove confirmed unused endpoints
4. Update documentation

**Total endpoints in api.py**: 20 (after Telangana removal)
**Actually used**: 7 (frontend) + 3 (tests) = 10
**Unused**: 10 endpoints
