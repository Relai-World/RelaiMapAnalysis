# 🚨 URGENT: Fix Connectivity Feature

## Problem
The connectivity feature is broken in production showing:
- "undefined" for all results
- "NaN km away" for distances
- Console errors: `origin=undefined,undefined`, `Invalid LngLat object: (NaN, NaN)`
- Properties panel shows "Loading..." indefinitely

## Root Cause
The Supabase function `get_properties_func` was updated to include `latitude` and `longitude` columns that **don't exist** in the `unified_data_DataType_Raghu` table. This causes the function to return NULL for these fields, breaking coordinate extraction.

## Solution

### Step 1: Fix Supabase Function (IMMEDIATE)
1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR_PROJECT/sql
2. Copy the entire contents of `FIX_SUPABASE_FUNCTION.sql`
3. Paste into SQL Editor
4. Click "Run" button
5. You should see: "Function restored to original working version!"

### Step 2: Verify Fix
1. Go to your deployed site: https://relaimapanalysis.onrender.com
2. Click on any location (e.g., Gachibowli)
3. Click on any property
4. Property details should now load correctly
5. Click "🚉 Show Connectivity" button
6. Should show nearest Railway, Metro, and Airport with routes

### Step 3: Verify Environment Variables
Make sure `GOOGLE_MAPS_API_KEY` is set in Render:
1. Go to Render Dashboard → Your Service → Environment
2. Check if `GOOGLE_MAPS_API_KEY` exists
3. If not, add it with your Google Maps API key

## How It Works Now

The connectivity feature extracts coordinates from the `google_place_location` field which contains:
- Google Maps URLs (format: `@17.4435,78.3772`)
- JSON strings (format: `{"lat": 17.4435, "lng": 78.3772}`)
- Raw coordinates (format: `17.4435, 78.3772`)

The `extractCoordinates()` function in `frontend/app.js` handles all these formats automatically.

## What NOT to Do

❌ **DO NOT** run `UPDATE_SUPABASE_FOR_CONNECTIVITY.sql` again
- This file tries to add `latitude`/`longitude` columns that don't exist
- It will break the function again

## Technical Details

### Original Working Function
```sql
CREATE OR REPLACE FUNCTION get_properties_func(area_name TEXT, bhk_filter TEXT DEFAULT NULL)
RETURNS TABLE (
    id INT,
    projectname TEXT,
    ...
    google_place_location TEXT,  -- ✅ This field exists
    full_details JSONB
)
```

### Broken Function (DO NOT USE)
```sql
CREATE OR REPLACE FUNCTION get_properties_func(area_name TEXT, bhk_filter TEXT DEFAULT NULL)
RETURNS TABLE (
    id INT,
    projectname TEXT,
    ...
    latitude FLOAT,   -- ❌ This column doesn't exist in table
    longitude FLOAT,  -- ❌ This column doesn't exist in table
    full_details JSONB
)
```

## Files Involved
- ✅ `FIX_SUPABASE_FUNCTION.sql` - Run this to fix
- ❌ `UPDATE_SUPABASE_FOR_CONNECTIVITY.sql` - DO NOT run this
- 📄 `frontend/app.js` - Contains coordinate extraction logic
- 📄 `api.py` - Contains `/api/nearby-places` endpoint

## After Fix is Applied

The connectivity feature will:
1. Extract coordinates from `google_place_location` field
2. Call `/api/nearby-places` with proper lat/lng
3. Show nearest Railway Station (🚂 Orange)
4. Show nearest Metro Station (🚇 Purple)
5. Show nearest Airport (✈️ Blue)
6. Draw all 3 routes simultaneously with colored lines
7. Display compact teardrop pins with auto-open popups
