# Map Data Source Analysis

## Summary

I've verified how your map location points and search function work with the database tables.

---

## 🗺️ Map Location Points

**Status:** ✅ **Uses `locations` table**

### How it works:

1. **Frontend** (`frontend/app.js` line 668):
   ```javascript
   const data = await insightsPromise;
   // insightsPromise = callSupabaseRPC('get_all_insights');
   ```

2. **RPC Function** (`supabase_functions.sql` line 49):
   ```sql
   CREATE OR REPLACE FUNCTION get_all_insights()
   ```

3. **Data Source**:
   - **Primary table:** `locations` (for coordinates & location names)
   - **Joined with:** `location_insights` (for sentiment/growth/investment scores)
   - **Joined with:** `unified_data_DataType_Raghu` (for property pricing data)
   - **Joined with:** `news_balanced_corpus_1` (for article counts)

4. **Map Rendering** (`frontend/app.js` line 806):
   ```javascript
   map.addSource("locations", {
     type: "geojson",
     data: {
       type: "FeatureCollection",
       features: data.map(d => ({
         type: "Feature",
         geometry: { type: "Point", coordinates: [d.longitude, d.latitude] },
         properties: d
       }))
     }
   });
   ```

**Result:** 346 location points displayed on the map

---

## 🔍 Search Function

**Status:** ⚠️ **Uses `news_balanced_corpus_1` table (NOT `locations`)**

### How it works:

1. **Frontend** (`frontend/app.js` line 713):
   ```javascript
   const matches = await callSupabaseRPC('search_locations_func', { search_query: val });
   ```

2. **RPC Function** (`supabase_functions.sql` line 157):
   ```sql
   CREATE OR REPLACE FUNCTION search_locations_func(search_query TEXT)
   ```

3. **Data Source**:
   - **Primary table:** `news_balanced_corpus_1` (searches `location_name` column)
   - **Does NOT query:** `locations` table directly

4. **Search Logic** (`frontend/app.js` line 730):
   ```javascript
   // After getting search results from news_balanced_corpus_1,
   // tries to match with insights data (which comes from locations table)
   const insightMatch = Array.isArray(data)
     ? data.find(d => d.location.toLowerCase() === match.location_name.toLowerCase())
     : null;
   ```

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MAP LOCATION POINTS                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              callSupabaseRPC('get_all_insights')
                            │
                            ▼
              ┌─────────────────────────────┐
              │  get_all_insights() RPC     │
              └─────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌──────────────┐      ┌──────────────────┐
        │  locations   │      │ location_insights│
        │  (PRIMARY)   │◄─────┤  (scores)        │
        └──────────────┘      └──────────────────┘
                │
                ├──────► unified_data_DataType_Raghu (properties)
                │
                └──────► news_balanced_corpus_1 (article counts)


┌─────────────────────────────────────────────────────────────┐
│                     SEARCH FUNCTION                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        callSupabaseRPC('search_locations_func')
                            │
                            ▼
              ┌─────────────────────────────┐
              │ search_locations_func() RPC │
              └─────────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────────┐
              │  news_balanced_corpus_1      │
              │  (searches location_name)    │
              └──────────────────────────────┘
                            │
                            ▼
              Frontend matches with insights data
                  (from locations table)
```

---

## 📊 Verification Results

Ran `verify_map_data_source.py`:

```
✅ MAP LOCATION POINTS: Use 'locations' table (via get_all_insights RPC)
   - Returns: 346 locations
   - Sample: Abids (78.477182, 17.3894783)

⚠️  SEARCH FUNCTION: Uses 'news_balanced_corpus_1' table (NOT locations!)
   - Returns: location_name + location_id
   - Sample search for 'gachi': Found "Gachibowli"
```

---

## 💡 Recommendation

~~The search function currently queries `news_balanced_corpus_1` instead of the `locations` table.~~

### ✅ FIX APPLIED

The search function has been updated to query the `locations` table directly.

**Status**: ✅ FIXED in `supabase_functions.sql` (line 157)

The function now correctly uses:
```sql
FROM locations l
WHERE l.name ILIKE '%' || search_query || '%'
```

Instead of the old incorrect query:
```sql
FROM news_balanced_corpus_1 nbc
WHERE nbc.location_name ILIKE '%' || search_query || '%'
```

### Verification:
- ✅ Search for 'gachi' returns: Gachibowli
- ✅ Search for 'kond' returns: Kondapur, Manikonda
- ✅ Search for 'banj' returns: Banjara Hills

---

## ✅ Conclusion

- **Map location points:** ✅ Correctly use `locations` table
- **Search function:** ✅ NOW FIXED - Uses `locations` table
- **Architecture:** ✅ Both features use the same authoritative source
- **news_balanced_corpus_1:** ✅ Reserved for sentiment analysis only
