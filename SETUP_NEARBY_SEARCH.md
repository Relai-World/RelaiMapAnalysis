# Setup Nearby Search Feature

## Problem
The nearby locations feature isn't working because the SQL functions haven't been created in Supabase yet.

## Solution
You need to run the SQL functions in your Supabase database.

## Steps to Fix

### 1. Open Supabase SQL Editor
1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New query"

### 2. Run the SQL File
1. Open the file `RUN_THIS_FOR_NEARBY_SEARCH.sql` in this project
2. Copy ALL the content from that file
3. Paste it into the Supabase SQL Editor
4. Click "Run" button (or press Ctrl+Enter / Cmd+Enter)

### 3. Verify Success
After running the SQL, you should see test results showing:
- ✅ Nearby locations for Kokapet, Hyderabad
- ✅ Nearby properties for Gachibowli, Hyderabad  
- ✅ Nearby locations for Whitefield, Bangalore
- ✅ Nearby properties for Whitefield, Bangalore
- ✅ Success message

### 4. Test in Frontend
1. Refresh your web application
2. Search for "Kokapet" in the global search bar
3. You should now see "Nearby (within 1km)" section with nearby locations
4. Each nearby location will show the distance in km

## What This Does

The SQL file creates 4 functions:

1. **extract_lat()** - Helper to extract latitude from property coordinates
2. **extract_lng()** - Helper to extract longitude from property coordinates
3. **search_nearby_locations_func()** - Finds locations within 1km radius
4. **search_nearby_properties_func()** - Finds properties within 1km radius

## How It Works

When you search for a location:
1. The app finds matching locations
2. For the first match, it gets the coordinates (latitude/longitude)
3. It calls `search_nearby_locations_func()` with those coordinates
4. The function uses Haversine formula to calculate distances
5. Returns locations within 1km, sorted by distance
6. Frontend displays them under "Nearby (within 1km)" divider

## Works for Both Cities

The functions work for:
- ✅ Hyderabad locations and properties
- ✅ Bangalore locations and properties

The `locations` table has data for both cities, so nearby search will work everywhere!
