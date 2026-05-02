# FastAPI Implementation Steps

## You're using FastAPI (not Flask)!

Your `api.py` uses FastAPI, so the implementation is slightly different.

## Step 1: Add Test Endpoint (2 minutes)

Open `api.py` and add this code (copy from `test_amenities_fastapi.py`):

```python
from pydantic import BaseModel

class AmenitiesRequest(BaseModel):
    area_name: str
    radius: int = 1000
    property_id: int

@app.post("/api/nearby-amenities")
async def get_nearby_amenities(request: AmenitiesRequest):
    """TEST ENDPOINT - Returns mock data"""
    print(f"📍 Received: {request.area_name}, property: {request.property_id}")
    
    return {
        'hospitals_count': 5,
        'shopping_malls_count': 3,
        'schools_count': 8,
        'restaurants_count': 25,
        'metro_stations_count': 2,
        'total_count': 43,
        'area_name': request.area_name
    }
```

## Step 2: Restart Backend

```bash
# Stop your current backend (Ctrl+C)
# Start it again
python api.py
# or
uvicorn api:app --reload
```

## Step 3: Test in Browser

1. Refresh your frontend page (Ctrl+Shift+R to clear cache)
2. Open comparison modal
3. You should see: **"43 amenities nearby"**

If this works, the connection is good! ✅

## Step 4: Implement Real Endpoint

Once test works, replace the test endpoint with the real one from `add_amenities_endpoint_fastapi.py`.

The real endpoint:
1. Looks up coordinates from locations table
2. Calls Google Places API
3. Stores counts in database
4. Returns results

## Common Issues

### Issue: Still shows "Unable to fetch"

**Check:**
1. Is backend running? Look for: `Uvicorn running on http://...`
2. What port? Should be same as frontend expects
3. Any errors in backend console?

**Fix:**
- Make sure backend is running
- Check backend console for errors
- Try the test endpoint first

### Issue: CORS Error

FastAPI CORS is already configured in your `api.py`, so this should work.

If you see CORS errors, check that your frontend origin is in the allowed list.

### Issue: 422 Unprocessable Entity

This means the request format is wrong. Check:
- Request should be JSON
- Should have: `area_name`, `radius`, `property_id`

## Verification

### Backend Console Should Show:
```
📍 Received: Hitec City, property: 123
```

### Frontend Should Show:
```
43 amenities nearby
```

### Browser Console Should Show:
```
✅ Fetched and stored amenities for property 123 (Hitec City): 43 total
```

## Next Steps

1. ✅ Add test endpoint to `api.py`
2. ✅ Restart backend
3. ✅ Test in browser - should see "43 amenities nearby"
4. ⏳ If test works, implement real endpoint
5. ⏳ Get Google Places API key
6. ⏳ Add to `.env` file

## Files

- `test_amenities_fastapi.py` - Test endpoint (use this first!)
- `add_amenities_endpoint_fastapi.py` - Real endpoint (use after test works)
- `api.py` - Your FastAPI app (add endpoint here)

## Quick Copy-Paste

Just add this to your `api.py` file:

```python
# Add after your imports
from pydantic import BaseModel

# Add this model
class AmenitiesRequest(BaseModel):
    area_name: str
    radius: int = 1000
    property_id: int

# Add this endpoint (anywhere after app = FastAPI(...))
@app.post("/api/nearby-amenities")
async def get_nearby_amenities(request: AmenitiesRequest):
    print(f"📍 Request: {request.area_name}, property: {request.property_id}")
    return {
        'hospitals_count': 5,
        'shopping_malls_count': 3,
        'schools_count': 8,
        'restaurants_count': 25,
        'metro_stations_count': 2,
        'total_count': 43,
        'area_name': request.area_name
    }
```

That's it! Restart backend and test.
