# Google Places API Integration for Amenities

## Overview
This guide explains how to implement the Google Places API fallback for properties without stored amenities data.

## Current Implementation Status
✅ Frontend placeholder logic implemented
✅ Coordinate parsing from multiple formats
⏳ Backend API endpoint needed
⏳ Google Places API integration needed

## Architecture

```
Property Data
    ↓
Check external_amenities field
    ↓
    ├─ Has amenities? → Display them
    ↓
    └─ No amenities? → Check coordinates
           ↓
           ├─ Has coordinates? → Call backend API
           │      ↓
           │      Backend calls Google Places API
           │      ↓
           │      Return nearby amenities
           │      ↓
           │      Update UI
           ↓
           └─ No coordinates? → Display "N/A"
```

## Step 1: Get Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Places API"
4. Create API credentials (API Key)
5. Restrict the API key to:
   - Places API
   - Your server IP addresses (for security)

## Step 2: Backend Implementation (Python/Flask)

Add to `api.py`:

```python
import os
import requests
from flask import request, jsonify

# Get API key from environment variable
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

@app.route('/api/nearby-amenities', methods=['POST'])
def get_nearby_amenities():
    """
    Fetch nearby amenities using Google Places API
    
    Request body:
    {
        "lat": 17.4485,
        "lng": 78.3908,
        "radius": 1000  # optional, default 1000 meters
    }
    
    Response:
    {
        "amenities": ["School", "Hospital", "Shopping Mall", ...],
        "count": 15
    }
    """
    try:
        data = request.json
        lat = data.get('lat')
        lng = data.get('lng')
        radius = data.get('radius', 1000)  # Default 1km radius
        
        if not lat or not lng:
            return jsonify({'error': 'Missing lat or lng'}), 400
        
        # Call Google Places API - Nearby Search
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'location': f'{lat},{lng}',
            'radius': radius,
            'key': GOOGLE_PLACES_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        places_data = response.json()
        
        if places_data.get('status') != 'OK':
            return jsonify({
                'error': f"Google Places API error: {places_data.get('status')}",
                'amenities': [],
                'count': 0
            }), 200
        
        # Extract unique amenity types
        amenity_types = set()
        for place in places_data.get('results', []):
            types = place.get('types', [])
            for place_type in types:
                # Filter out generic types
                if place_type not in ['point_of_interest', 'establishment']:
                    # Convert snake_case to Title Case
                    readable_type = place_type.replace('_', ' ').title()
                    amenity_types.add(readable_type)
        
        amenities_list = sorted(list(amenity_types))
        
        return jsonify({
            'amenities': amenities_list,
            'count': len(amenities_list)
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f'API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
```

## Step 3: Environment Configuration

Add to `.env`:
```bash
GOOGLE_PLACES_API_KEY=your_api_key_here
```

## Step 4: Frontend Implementation

Update `fetchAmenitiesFromGoogle()` in `frontend/comparison-ui.js`:

```javascript
async fetchAmenitiesFromGoogle(properties) {
  const amenitiesLoadingSpans = document.querySelectorAll('.amenities-loading');
  
  for (const span of amenitiesLoadingSpans) {
    const index = parseInt(span.dataset.propertyIndex);
    const property = properties[index];
    
    if (!property) continue;
    
    // Get coordinates
    let lat, lng;
    const location = property.google_place_location || property.full_details?.google_place_location;
    
    if (location) {
      try {
        // Parse coordinates
        if (typeof location === 'string') {
          if (location.startsWith('{')) {
            const parsed = JSON.parse(location.replace(/'/g, '"'));
            lat = parsed.lat;
            lng = parsed.lng;
          } else if (location.includes(',')) {
            const parts = location.split(',');
            lat = parseFloat(parts[0]);
            lng = parseFloat(parts[1]);
          }
        } else if (typeof location === 'object') {
          lat = location.lat;
          lng = location.lng;
        }
        
        if (lat && lng) {
          // Fetch nearby amenities from backend
          span.textContent = 'Fetching nearby amenities...';
          
          try {
            const response = await fetch('/api/nearby-amenities', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ lat, lng, radius: 1000 })
            });
            
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
              span.textContent = 'Unable to fetch amenities';
              console.error('Amenities API error:', data.error);
            } else if (data.amenities && data.amenities.length > 0) {
              // Display first 5 amenities
              const displayAmenities = data.amenities.slice(0, 5).join(', ');
              const moreCount = data.amenities.length - 5;
              span.textContent = displayAmenities + (moreCount > 0 ? ` +${moreCount} more` : '');
            } else {
              span.textContent = 'No nearby amenities found';
            }
            
          } catch (fetchError) {
            console.error('Failed to fetch amenities:', fetchError);
            span.textContent = 'Unable to fetch amenities';
          }
          
        } else {
          span.textContent = 'Location data unavailable';
        }
      } catch (e) {
        console.error('Failed to parse location:', e);
        span.textContent = 'Location data unavailable';
      }
    } else {
      span.textContent = 'Location data unavailable';
    }
  }
}
```

## Step 5: Testing

### Test Backend Endpoint
```bash
curl -X POST http://localhost:5000/api/nearby-amenities \
  -H "Content-Type: application/json" \
  -d '{"lat": 17.4485, "lng": 78.3908, "radius": 1000}'
```

Expected response:
```json
{
  "amenities": ["School", "Hospital", "Shopping Mall", "Restaurant", ...],
  "count": 15
}
```

### Test Frontend
1. Open browser console
2. Load the test script: `test_comparison_fields.js`
3. Run: `testComparisonFields()`
4. Open comparison modal
5. Verify amenities are fetched for properties without stored data

## Step 6: Optimization (Optional)

### Cache Results
Add caching to avoid repeated API calls:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache for 24 hours
amenities_cache = {}
CACHE_DURATION = timedelta(hours=24)

def get_cached_amenities(lat, lng, radius):
    cache_key = f"{lat},{lng},{radius}"
    
    if cache_key in amenities_cache:
        cached_data, timestamp = amenities_cache[cache_key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return cached_data
    
    return None

def set_cached_amenities(lat, lng, radius, data):
    cache_key = f"{lat},{lng},{radius}"
    amenities_cache[cache_key] = (data, datetime.now())
```

### Rate Limiting
Add rate limiting to prevent API quota exhaustion:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/nearby-amenities', methods=['POST'])
@limiter.limit("10 per minute")
def get_nearby_amenities():
    # ... implementation
```

## Cost Considerations

### Google Places API Pricing (as of 2024)
- Nearby Search: $32 per 1,000 requests
- Free tier: $200 credit per month (~6,250 requests)

### Optimization Strategies
1. **Cache results** for 24 hours (reduces API calls by ~95%)
2. **Batch requests** when possible
3. **Store results** in database after first fetch
4. **Use smaller radius** (500m instead of 1000m)
5. **Limit to essential amenity types** only

### Example: Update Database with Fetched Amenities
```python
# After successful API call, store in database
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Update property with fetched amenities
supabase.table('unified_data_DataType_Raghu').update({
    'external_amenities': ', '.join(amenities_list)
}).eq('id', property_id).execute()
```

## Security Best Practices

1. **Never expose API key in frontend code**
2. **Use environment variables** for API keys
3. **Restrict API key** to specific APIs and IP addresses
4. **Implement rate limiting** on backend endpoint
5. **Validate input** (lat/lng ranges, radius limits)
6. **Add authentication** if needed (require user login)

## Troubleshooting

### Issue: "API key not valid"
- Check API key is correct in `.env`
- Verify Places API is enabled in Google Cloud Console
- Check API key restrictions

### Issue: "OVER_QUERY_LIMIT"
- You've exceeded your quota
- Implement caching
- Reduce request frequency
- Upgrade Google Cloud billing

### Issue: "ZERO_RESULTS"
- Location has no nearby places
- Try increasing radius
- Verify coordinates are correct

### Issue: Frontend shows "Loading..." forever
- Check browser console for errors
- Verify backend endpoint is running
- Check CORS settings if needed
- Verify API endpoint URL is correct

## Alternative: Use Existing Data

If Google Places API is too expensive, consider:

1. **Pre-populate amenities** during data scraping
2. **Use OpenStreetMap API** (free, but less comprehensive)
3. **Manual data entry** for key properties
4. **Show "Contact for details"** instead of fetching

## Next Steps

1. ✅ Get Google Places API key
2. ✅ Add backend endpoint to `api.py`
3. ✅ Update `.env` with API key
4. ✅ Update frontend `fetchAmenitiesFromGoogle()`
5. ✅ Test with sample properties
6. ✅ Implement caching (optional)
7. ✅ Monitor API usage and costs
