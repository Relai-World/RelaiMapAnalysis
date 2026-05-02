# Quick Start: Amenities Count Feature (v2.8)

## What Was Implemented

✅ **Frontend** (v2.8) - Uses area name to fetch amenities (much simpler!)
✅ **Database Caching** - Stores counts in 5 columns for analytics
✅ **User Experience** - Shows total count with breakdown on hover

## Key Improvement in v2.8

**Now uses AREA NAME instead of coordinates!**
- Every property has area name (e.g., "Hitec City")
- Backend looks up coordinates from locations table
- No more "Location unavailable" errors!

## What You Need to Do

### Step 1: Get Google Places API Key (5 minutes)

1. Go to https://console.cloud.google.com/
2. Create/select project
3. Enable "Places API"
4. Create API Key
5. Copy the key

### Step 2: Add to Environment Variables (1 minute)

Edit `.env` file:
```bash
GOOGLE_PLACES_API_KEY=your_api_key_here
```

### Step 3: Add Backend Endpoint (10 minutes)

Copy the updated code from `BACKEND_AMENITIES_API.md` and add to `api.py`:

```python
@app.route('/api/nearby-amenities', methods=['POST'])
def get_nearby_amenities():
    # Get area name from request
    area_name = request.json.get('area_name')  # "Hitec City"
    
    # Look up coordinates from locations table
    result = supabase.table('hyderabad_locations')\
        .select('latitude, longitude')\
        .ilike('name', area_name)\
        .limit(1)\
        .execute()
    
    # ... see BACKEND_AMENITIES_API.md for full code
```

Install dependencies:
```bash
pip install requests supabase
```

### Step 4: Test (2 minutes)

1. Start your backend: `python api.py`
2. Open the map application
3. Add 2-3 properties to comparison (they all have area names!)
4. Click "Show Comparison"
5. Watch amenities count appear!

## Expected Result

### Desktop View
```
Nearby Amenities: 43 amenities nearby
                  [hover to see: 5 hospitals, 8 schools, 3 malls, 25 restaurants, 2 metro]
```

### Request Sent to Backend
```json
{
    "area_name": "Hitec City",
    "radius": 1000,
    "property_id": 123
}
```

### Backend Process
```
1. Receive "Hitec City"
2. Look up in hyderabad_locations table
3. Get lat=17.4485, lng=78.3908
4. Call Google Places API
5. Store counts in database
6. Return total count
```

## Cost

- **$0.16 per property** (5 API calls × $0.032)
- **Free tier**: $200/month = ~1,250 properties
- **Only charged when user compares** (not on page load)

## Database Columns Used

```sql
hospitals_count INTEGER          -- Already exists
shopping_malls_count INTEGER     -- Already exists
schools_count INTEGER            -- Already exists
restaurants_count INTEGER        -- Already exists
metro_stations_count INTEGER     -- Already exists
```

## Files to Reference

1. **BACKEND_AMENITIES_API.md** - Complete backend code
2. **AMENITIES_CACHING_IMPLEMENTATION.md** - Full implementation details
3. **frontend/comparison-ui.js** - Frontend code (already updated)

## Troubleshooting

### "Location unavailable"
- Property missing `google_place_location` field
- Check: `SELECT id, google_place_location FROM unified_data_DataType_Raghu WHERE id = 123`

### "Unable to fetch"
- Backend endpoint not running
- Google API key invalid
- Check console logs

### No counts in database
- Backend not storing (check logs)
- Supabase credentials wrong
- Check: `SELECT * FROM unified_data_DataType_Raghu WHERE id = 123`

## Support

- Backend implementation: See `BACKEND_AMENITIES_API.md`
- Full details: See `AMENITIES_CACHING_IMPLEMENTATION.md`
- Testing guide: See `TEST_AMENITIES_COUNT.md`

## Summary

✅ Frontend ready (v2.7)
⏳ Backend needs implementation (15 minutes)
⏳ Google API key needed (5 minutes)

**Total setup time: ~20 minutes**
