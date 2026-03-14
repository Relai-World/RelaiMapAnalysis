# What You're Actually Using

## 🎯 YOUR WEBSITE USES ONLY 7 ENDPOINTS

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND FEATURE          →  API ENDPOINT                  │
├─────────────────────────────────────────────────────────────┤
│  Page Load (map pins)      →  /api/v1/insights             │
│  Search Box                →  /api/v1/search               │
│  Properties Panel          →  /api/v1/properties           │
│  Property Detail Drawer    →  /api/v1/properties/{id}      │
│  Price Chart               →  /api/v1/location/{id}/trends │
│  Cost Statistics           →  /api/v1/property-costs/{name}│
│  Amenity Buttons           →  /api/v1/location/{id}/amenities/{type}│
└─────────────────────────────────────────────────────────────┘
```

## 📊 BREAKDOWN

### ✅ Core Location Data (2 endpoints)
1. `/api/v1/insights` - Main data (locations, sentiment, scores)
2. `/api/v1/search` - Search functionality

### ✅ Properties Feature (2 endpoints)
3. `/api/v1/properties` - List properties by area
4. `/api/v1/properties/{id}` - Single property details

### ✅ Analytics (3 endpoints)
5. `/api/v1/location/{id}/trends` - Price trends chart
6. `/api/v1/property-costs/{name}` - Cost statistics
7. `/api/v1/location/{id}/amenities/{type}` - Nearby amenities

---

## ❌ WHAT YOU'RE NOT USING (24 endpoints)

### Category 1: Debug/Testing (2)
- Health check
- Search debug

### Category 2: Alternative Data Views (4)
- Market trends (all locations average)
- All location costs (bulk)
- All property costs (bulk)
- Detailed area costs

### Category 3: Boundaries (3)
- Location boundaries from DB
- All boundaries
- Duplicate endpoint

### Category 4: Infrastructure (1)
- Old infrastructure endpoint (broken)

### Category 5: Telangana Gov Data (11)
- Complete government registration data feature
- Districts, mandals, villages
- Market values, price stats
- Search, boundaries

### Category 6: Misc (3)
- Various unused helpers

---

## 💡 RECOMMENDATION

**Keep**: 7 used endpoints + health check = 8 endpoints

**Remove**: 23 unused endpoints

**Result**: 
- Cleaner codebase
- Easier maintenance
- ~600 lines less code
- No impact on your website

---

## 🤔 DECISION POINT

**Telangana Registration Endpoints (11 total)**

These are a complete feature for government registration data.

**Keep them IF**:
- You plan to add gov registration data to your site
- You want district/mandal/village data
- You need official market values

**Remove them IF**:
- Not in your roadmap
- Focus is only on Hyderabad properties
- Want simpler codebase

---

**Want me to remove the unused endpoints?**
