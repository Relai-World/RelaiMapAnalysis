# Troubleshooting: "Unable to fetch" Error

## Current Status

✅ Frontend is working (v2.8)
✅ Area name is being sent ("Hitec City")
✅ API call is being made
❌ Backend is not responding correctly

## Error: "Unable to fetch"

This means the frontend is calling `/api/nearby-amenities` but getting an error.

## Step 1: Check Browser Console

1. Open browser console (F12)
2. Go to "Console" tab
3. Look for errors like:

```
❌ Failed to fetch amenities: TypeError: Failed to fetch
❌ Amenities API error: HTTP 404
❌ Amenities API error: HTTP 500
```

## Step 2: Check Network Tab

1. Open browser console (F12)
2. Go to "Network" tab
3. Filter by "nearby-amenities"
4. Click on the request
5. Check:
   - **Status**: Should be 200, might be 404 or 500
   - **Request URL**: Should be `http://localhost:5000/api/nearby-amenities`
   - **Request Payload**: Should show `{"area_name": "Hitec City", ...}`
   - **Response**: Shows the error message

## Common Issues

### Issue 1: Backend Not Running
**Symptom**: `Failed to fetch` or `net::ERR_CONNECTION_REFUSED`

**Solution**:
```bash
# Start the backend
python api.py

# Or use the test endpoint
python test_amenities_endpoint.py
```

### Issue 2: Endpoint Not Implemented
**Symptom**: `404 Not Found`

**Solution**: Add the endpoint to `api.py`:
```python
@app.route('/api/nearby-amenities', methods=['POST'])
def get_nearby_amenities():
    # ... see BACKEND_AMENITIES_API.md
```

### Issue 3: CORS Error
**Symptom**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**: Add CORS to your Flask app:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable CORS
```

Install CORS:
```bash
pip install flask-cors
```

### Issue 4: Wrong Port
**Symptom**: `Failed to fetch`

**Check**: What port is your backend running on?
- Frontend expects: `http://localhost:5000`
- If different, update frontend or backend

**Update frontend** (if backend is on different port):
```javascript
// In comparison-ui.js, change:
const response = await fetch('http://localhost:YOUR_PORT/api/nearby-amenities', {
```

### Issue 5: Missing Dependencies
**Symptom**: `500 Internal Server Error`

**Solution**: Install required packages:
```bash
pip install flask flask-cors requests supabase
```

## Quick Test: Use Mock Endpoint

To verify the connection works, use the test endpoint:

### Step 1: Run Test Server
```bash
python test_amenities_endpoint.py
```

You should see:
```
🚀 Starting test server on http://localhost:5000
📍 Endpoint: POST /api/nearby-amenities
```

### Step 2: Test from Browser
Open comparison modal and check if you see:
```
43 amenities nearby
```

If this works, the connection is fine and you just need to implement the real endpoint.

### Step 3: Test with curl
```bash
curl -X POST http://localhost:5000/api/nearby-amenities \
  -H "Content-Type: application/json" \
  -d '{"area_name": "Hitec City", "property_id": 123}'
```

Expected response:
```json
{
  "hospitals_count": 5,
  "shopping_malls_count": 3,
  "schools_count": 8,
  "restaurants_count": 25,
  "metro_stations_count": 2,
  "total_count": 43,
  "area_name": "Hitec City",
  "message": "Mock data - Google API not yet integrated"
}
```

## Debugging Checklist

- [ ] Backend server is running
- [ ] Backend is on port 5000 (or frontend updated to match)
- [ ] CORS is enabled on backend
- [ ] Endpoint `/api/nearby-amenities` exists
- [ ] Endpoint accepts POST requests
- [ ] Browser console shows no CORS errors
- [ ] Network tab shows request is being sent
- [ ] Network tab shows response (even if error)

## Next Steps Based on Error

### If you see "Failed to fetch"
→ Backend not running or wrong port

### If you see "404 Not Found"
→ Endpoint not implemented in api.py

### If you see "500 Internal Server Error"
→ Backend error, check backend console logs

### If you see "CORS error"
→ Add `flask-cors` to backend

### If test endpoint works but real endpoint doesn't
→ Issue with Google Places API integration or Supabase connection

## Get More Help

Share the following:
1. Browser console error message
2. Network tab response
3. Backend console output
4. What port is your backend running on?

## Files to Check

1. `api.py` - Does it have the `/api/nearby-amenities` endpoint?
2. `test_amenities_endpoint.py` - Use this to test connection
3. `BACKEND_AMENITIES_API.md` - Full implementation guide
4. Browser console - Shows exact error
5. Network tab - Shows request/response details
