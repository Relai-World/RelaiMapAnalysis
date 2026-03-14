# Endpoint Comparison: location-costs vs property-costs

## 🔍 THE DIFFERENCE

### `/api/v1/location-costs/{name}` (Line 541)
**Returns**: Basic cost statistics
```json
{
  "location": "Gachibowli",
  "count": 150,
  "avgBase": 2.5,
  "avgSqft": 8500,
  "minBase": 1.2,
  "maxBase": 5.0,
  "minSqft": 5000,
  "maxSqft": 12000
}
```

### `/api/v1/property-costs/{name}` (Line 675)
**Returns**: DETAILED statistics + extra data
```json
{
  "area_name": "Gachibowli",
  "city": "Hyderabad",
  "property_count": 150,
  "avg_price_per_sft": 8500,
  "min_price_per_sft": 5000,
  "max_price_per_sft": 12000,
  "avg_base_price": 2.5,
  "min_base_price": 1.2,
  "max_base_price": 5.0,
  "builder_count": 25,           ← EXTRA
  "project_count": 45,            ← EXTRA
  "builders": "Builder1, Builder2...",  ← EXTRA
  "price_range": "₹5,000 - ₹12,000/sqft",  ← EXTRA
  "sample_properties": [...]      ← EXTRA (top 5 properties)
}
```

## 📊 KEY DIFFERENCES

| Feature | location-costs | property-costs |
|---------|---------------|----------------|
| Basic prices | ✅ | ✅ |
| Builder count | ❌ | ✅ |
| Project count | ❌ | ✅ |
| Builders list | ❌ | ✅ |
| Price range string | ❌ | ✅ |
| Sample properties | ❌ | ✅ (top 5) |
| Response format | Simple | Detailed |

## 🎯 USAGE

### Frontend Uses:
- **`/api/v1/property-costs/{name}`** (line 2112 in app.js)
- Needs the detailed version with all extra data

### Test Files Use:
- **`/api/v1/location-costs/{name}`** (utilities/test_all_endpoints.py)
- Uses the simpler version

## ✅ VERDICT

**These are NOT duplicates!**

- `location-costs/{name}` = Simple/basic version
- `property-costs/{name}` = Detailed/enhanced version

**Frontend needs the detailed one** because it displays:
- Property count badge
- Builder information
- Sample properties
- Formatted price ranges

## 🤔 DECISION

### Option 1: Keep Both
- Frontend uses detailed version
- Tests use simple version
- Both serve different purposes

### Option 2: Consolidate
- Remove simple version
- Update tests to use detailed version
- Less code to maintain

### Option 3: Make Simple Version Return Detailed
- Merge the logic
- One endpoint, detailed response
- Update all callers

## 📝 RECOMMENDATION

**Keep both for now** because:
1. Frontend specifically uses property-costs (detailed)
2. Tests use location-costs (simple)
3. Different use cases
4. No harm in having both

**OR**

**Remove location-costs** and update test files to use property-costs instead (1 line change in test file).

---

## 🎯 FINAL ENDPOINT COUNT

### ✅ USED BY FRONTEND (7)
1. /api/v1/insights
2. /api/v1/search
3. /api/v1/properties
4. /api/v1/properties/{id}
5. /api/v1/location/{id}/trends
6. /api/v1/property-costs/{name} ← DETAILED VERSION
7. /api/v1/location/{id}/amenities/{type}

### 🧪 USED BY TESTS ONLY (3)
8. /api/v1/location-costs (bulk)
9. /api/v1/location-costs/{name} ← SIMPLE VERSION
10. /api/v1/location/{id}/infra

### 🔧 UTILITY (2)
11. / (health check)
12. /api/v1/search/debug

### ❌ UNUSED (8)
13. /api/v1/market-trends
14. /api/v1/property-costs (bulk - no {name})
15-24. Telangana endpoints (ALREADY REMOVED)

**Total: 20 endpoints remaining**
**Actually used: 10 (7 frontend + 3 tests)**
**Unused: 10**
