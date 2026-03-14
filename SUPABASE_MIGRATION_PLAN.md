# Supabase REST API Migration Plan

## 🎯 Goal
Migrate from `psycopg2` (direct PostgreSQL) to Supabase REST API using your anon key.

---

## ⚠️ IMPORTANT LIMITATIONS

### What Supabase REST API CAN'T Do:
- ❌ Complex CTEs (WITH clauses)
- ❌ Multi-table JOINs with complex conditions
- ❌ PostGIS functions (ST_X, ST_Y, ST_AsGeoJSON)
- ❌ Dynamic SQL
- ❌ Complex aggregations

### Solution: Use RPC (Remote Procedure Calls)
- ✅ Create PostgreSQL functions in Supabase
- ✅ Call them via REST API using anon key
- ✅ Keep all complex logic in database
- ✅ Simple Python code

---

## 📋 STEP-BY-STEP MIGRATION

### Step 1: Create PostgreSQL Functions in Supabase

1. **Go to Supabase Dashboard**:
   ```
   https://supabase.com/dashboard/project/ihraowxbduhlichzszgk/editor
   ```

2. **Click "SQL Editor"** (left sidebar)

3. **Copy and paste** the entire content of `supabase_functions.sql`

4. **Click "Run"** to create all functions

5. **Verify** functions are created (you should see success messages)

---

### Step 2: Update Python Code

I'll rewrite `api.py` to use Supabase client instead of psycopg2.

**Changes**:
- Remove `psycopg2` imports
- Remove `get_db()` function
- Use `get_supabase()` for all queries
- Call RPC functions instead of raw SQL

---

### Step 3: Test Each Endpoint

Test these endpoints after migration:
1. `/api/v1/insights` - Main data
2. `/api/v1/search` - Location search
3. `/api/v1/location/{id}/trends` - Price trends
4. `/api/v1/property-costs/{name}` - Property costs
5. `/api/v1/properties` - Properties list
6. `/api/v1/properties/{id}` - Property details
7. `/api/v1/location/{id}/amenities/{type}` - Amenities

---

## 🚨 CRITICAL ISSUES TO SOLVE

### Issue 1: Properties Endpoint
Your properties endpoint has VERY complex filtering logic:
```python
cur.execute("""
    SELECT * FROM unified_data_DataType_Raghu
    WHERE (LOWER(areaname) = LOWER(%s)
           OR LOWER(REPLACE(areaname, ' ', '')) = LOWER(REPLACE(%s, ' ', ''))
           OR areaname ILIKE %s
           OR %s ILIKE areaname)
    AND bhk = %s
    ORDER BY price_per_sft DESC
""")
```

**Solution**: Create RPC function for this too.

### Issue 2: Amenities Endpoint
Uses PostGIS and complex spatial queries.

**Solution**: Create RPC function or simplify logic.

### Issue 3: Property Detail
Needs to fetch single property with all fields.

**Solution**: Simple Supabase query (this one is easy).

---

## 📊 MIGRATION COMPLEXITY

### Easy to Migrate (Simple queries):
- ✅ `/api/v1/search/debug` - Table counts
- ✅ `/api/v1/properties/{id}` - Single property

### Medium (Need RPC functions):
- 🟡 `/api/v1/insights` - Complex CTEs
- 🟡 `/api/v1/search` - Location search
- 🟡 `/api/v1/location/{id}/trends` - Price trends
- 🟡 `/api/v1/property-costs/{name}` - Property costs

### Hard (Complex logic):
- 🔴 `/api/v1/properties` - Complex filtering + BHK logic
- 🔴 `/api/v1/location/{id}/amenities/{type}` - PostGIS + Overpass API

---

## ⏱️ ESTIMATED TIME

- **Create RPC functions**: 30 minutes
- **Rewrite api.py**: 2-3 hours
- **Test all endpoints**: 1-2 hours
- **Fix bugs**: 1-2 hours

**Total**: 5-8 hours of work

---

## 💡 ALTERNATIVE: Just Get the Password

**Time**: 2 minutes  
**Risk**: Zero  
**Code changes**: Zero  
**Functionality**: 100% preserved

---

## 🤔 MY RECOMMENDATION

**Before you spend 8 hours rewriting**:

1. Try to get the database password one more time
2. Check if `Ramesh@1545` is really wrong
3. Try resetting the password in Supabase dashboard
4. Contact your Supabase project admin

**If you absolutely cannot get the password**, then proceed with RPC migration.

---

## 🚀 READY TO PROCEED?

Tell me:
1. Did you create the RPC functions in Supabase?
2. Do you want me to rewrite `api.py` now?
3. Or do you want to try getting the password first?
