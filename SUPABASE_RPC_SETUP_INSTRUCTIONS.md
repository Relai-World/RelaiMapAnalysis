# Supabase RPC Functions Setup Instructions

## What Was Fixed

The `supabase_functions.sql` file has been updated to fix:

1. **Table name case sensitivity** - Changed `unified_data_DataType_Raghu` to `"unified_data_DataType_Raghu"` (quoted to preserve case)
2. **Ambiguous column reference** - Renamed `location_name` variable to `loc_name` in `get_location_trends_func()` to avoid conflict with table column

## Steps to Deploy

1. **Open Supabase SQL Editor**
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor

2. **Run the Updated SQL File**
   - Copy the entire contents of `supabase_functions.sql`
   - Paste into SQL Editor
   - Click "Run" or press Ctrl+Enter

3. **Verify Functions Were Created**
   - You should see success messages for all 6 functions
   - Check Database → Functions in Supabase dashboard

## Testing

After running the SQL file, test the functions:

```bash
python test_supabase_rpc_functions.py
```

Expected results:
- ✅ `get_all_insights()` - Returns all location data with summaries
- ✅ `search_locations_func()` - Returns matching locations
- ✅ `get_location_trends_func()` - Returns price trends with CAGR
- ✅ `get_property_costs_func()` - Returns property cost statistics
- ✅ `get_properties_func()` - Returns properties list
- ✅ `get_property_by_id_func()` - Returns single property details

## Functions Created

1. **`get_all_insights()`**
   - Endpoint equivalent: `/api/v1/insights`
   - Returns: All locations with sentiment/growth/investment scores and summaries

2. **`search_locations_func(search_query TEXT)`**
   - Endpoint equivalent: `/api/v1/search?q=<query>`
   - Returns: Matching location names and IDs

3. **`get_location_trends_func(loc_id INT)`**
   - Endpoint equivalent: `/api/v1/location/{location_id}/trends`
   - Returns: Price trends, CAGR, YoY growth

4. **`get_property_costs_func(area_name TEXT)`**
   - Endpoint equivalent: `/api/v1/property-costs/{area_name}`
   - Returns: Property cost statistics with min/max base prices

5. **`get_properties_func(area_name TEXT, bhk_filter TEXT)`**
   - Endpoint equivalent: `/api/v1/properties?area=<area>&bhk=<bhk>`
   - Returns: Properties list with optional BHK filter

6. **`get_property_by_id_func(prop_id INT)`**
   - Endpoint equivalent: `/api/v1/properties/{property_id}`
   - Returns: Single property details

## How to Call These Functions

### Using REST API (with anon key)

```bash
# Example: Get all insights
curl -X POST \
  'https://ihraowxbduhlichzszgk.supabase.co/rest/v1/rpc/get_all_insights' \
  -H 'apikey: YOUR_ANON_KEY' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{}'

# Example: Search locations
curl -X POST \
  'https://ihraowxbduhlichzszgk.supabase.co/rest/v1/rpc/search_locations_func' \
  -H 'apikey: YOUR_ANON_KEY' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"search_query": "gachibowli"}'

# Example: Get properties
curl -X POST \
  'https://ihraowxbduhlichzszgk.supabase.co/rest/v1/rpc/get_properties_func' \
  -H 'apikey: YOUR_ANON_KEY' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"area_name": "Gachibowli", "bhk_filter": "3"}'
```

### Using Python (supabase-py)

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get all insights
insights = supabase.rpc('get_all_insights').execute()

# Search locations
results = supabase.rpc('search_locations_func', {'search_query': 'gachi'}).execute()

# Get properties
properties = supabase.rpc('get_properties_func', {
    'area_name': 'Gachibowli',
    'bhk_filter': '3'
}).execute()
```

## Important Notes

1. **Read-Only Functions** - All functions are read-only and safe for anon access
2. **No Password Required** - Uses anon key, no database password needed
3. **Summary Fields** - Fetches `sentiment_summary`, `growth_summary`, `invest_summary` from `location_insights` table
4. **Amenities Endpoint** - The `/api/v1/location/{id}/amenities/{type}` endpoint uses Google Places API and cannot be replicated in SQL (keep in Python API)
5. **No Impact on Other Projects** - These are just read-only functions, won't affect other applications

## Troubleshooting

If you get errors:

1. **"relation does not exist"** - Table name case sensitivity issue, make sure quotes are used
2. **"column reference is ambiguous"** - Variable name conflicts with column name
3. **"permission denied"** - Make sure GRANT statements ran successfully
4. **"function does not exist"** - Function wasn't created, check for SQL errors

## Next Steps

After successful testing:
1. Update your `api.py` to use Supabase RPC calls instead of direct psycopg2
2. Or keep current API and use these functions as backup/alternative
3. Deploy to production with confidence - no password authentication issues!
