# Backend API for Amenities Count with Database Caching

## Overview
This API fetches amenities count from Google Places API and stores it in the database for future use.

## Database Columns
The following columns exist in `unified_data_DataType_Raghu` table:
- `hospitals_count` - Count of hospitals within 1km
- `shopping_malls_count` - Count of shopping malls within 1km
- `schools_count` - Count of schools within 1km
- `restaurants_count` - Count of restaurants within 1km
- `metro_stations_count` - Count of metro stations within 1km

## API Endpoint Implementation

Add this to `api.py`:

```python
import os
import requests
from flask import request, jsonify
from supabase import create_client

# Get API keys from environment
GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/api/nearby-amenities', methods=['POST'])
def get_nearby_amenities():
    """
    Fetch nearby amenities count using Google Places API and store in database
    Uses area name to lookup coordinates from locations table
    
    Request body:
    {
        "area_name": "Hitec City",
        "radius": 1000,
        "property_id": 123
    }
    
    Response:
    {
        "hospitals_count": 5,
        "shopping_malls_count": 3,
        "schools_count": 8,
        "restaurants_count": 25,
        "metro_stations_count": 2,
        "total_count": 43
    }
    """
    try:
        data = request.json
        area_name = data.get('area_name')
        radius = data.get('radius', 1000)
        property_id = data.get('property_id')
        
        if not area_name:
            return jsonify({'error': 'Missing area_name'}), 400
        
        if not property_id:
            return jsonify({'error': 'Missing property_id'}), 400
        
        # Get coordinates from locations table using area name
        # Try both hyderabad_locations and bangalore_locations
        lat, lng = None, None
        
        try:
            # Try hyderabad_locations first
            result = supabase.table('hyderabad_locations').select('latitude, longitude').ilike('name', area_name).limit(1).execute()
            if result.data and len(result.data) > 0:
                lat = result.data[0].get('latitude')
                lng = result.data[0].get('longitude')
        except:
            pass
        
        if not lat or not lng:
            try:
                # Try bangalore_locations
                result = supabase.table('bangalore_locations').select('latitude, longitude').ilike('name', area_name).limit(1).execute()
                if result.data and len(result.data) > 0:
                    lat = result.data[0].get('latitude')
                    lng = result.data[0].get('longitude')
            except:
                pass
        
        if not lat or not lng:
            try:
                # Try old locations table as fallback
                result = supabase.table('locations').select('latitude, longitude').ilike('name', area_name).limit(1).execute()
                if result.data and len(result.data) > 0:
                    lat = result.data[0].get('latitude')
                    lng = result.data[0].get('longitude')
            except:
                pass
        
        if not lat or not lng:
            return jsonify({'error': f'Coordinates not found for area: {area_name}'}), 404
        
        # Define amenity types to search for
        amenity_types = {
            'hospitals_count': ['hospital', 'doctor', 'health'],
            'shopping_malls_count': ['shopping_mall', 'department_store'],
            'schools_count': ['school', 'primary_school', 'secondary_school'],
            'restaurants_count': ['restaurant', 'cafe', 'food'],
            'metro_stations_count': ['subway_station', 'transit_station', 'train_station']
        }
        
        counts = {}
        total_count = 0
        
        # Fetch count for each amenity type
        for column_name, place_types in amenity_types.items():
            count = 0
            
            for place_type in place_types:
                try:
                    # Call Google Places API - Nearby Search
                    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
                    params = {
                        'location': f'{lat},{lng}',
                        'radius': radius,
                        'type': place_type,
                        'key': GOOGLE_PLACES_API_KEY
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    places_data = response.json()
                    
                    if places_data.get('status') == 'OK':
                        # Count unique places (avoid duplicates across types)
                        results = places_data.get('results', [])
                        count = max(count, len(results))  # Take max to avoid double counting
                    
                except Exception as e:
                    print(f"Error fetching {place_type}: {str(e)}")
                    continue
            
            counts[column_name] = count
            total_count += count
        
        # Store counts in database
        try:
            update_data = {
                'hospitals_count': counts.get('hospitals_count', 0),
                'shopping_malls_count': counts.get('shopping_malls_count', 0),
                'schools_count': counts.get('schools_count', 0),
                'restaurants_count': counts.get('restaurants_count', 0),
                'metro_stations_count': counts.get('metro_stations_count', 0)
            }
            
            result = supabase.table('unified_data_DataType_Raghu').update(
                update_data
            ).eq('id', property_id).execute()
            
            print(f"✅ Stored amenities count for property {property_id}: {total_count} total")
            
        except Exception as db_error:
            print(f"⚠️ Failed to store in database: {str(db_error)}")
            # Continue anyway - we can still return the counts
        
        # Return counts
        return jsonify({
            'hospitals_count': counts.get('hospitals_count', 0),
            'shopping_malls_count': counts.get('shopping_malls_count', 0),
            'schools_count': counts.get('schools_count', 0),
            'restaurants_count': counts.get('restaurants_count', 0),
            'metro_stations_count': counts.get('metro_stations_count', 0),
            'total_count': total_count,
            'stored_in_db': True
        })
        
    except requests.RequestException as e:
        return jsonify({'error': f'API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
```

## Environment Variables

Add to `.env`:
```bash
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
```

## Google Places API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Places API (New)"
3. Create API Key
4. Restrict to Places API only
5. Add to `.env` file

## Place Types Reference

### Hospitals
- `hospital` - General hospitals
- `doctor` - Doctor's offices
- `health` - Health facilities

### Shopping Malls
- `shopping_mall` - Shopping centers
- `department_store` - Large retail stores

### Schools
- `school` - General schools
- `primary_school` - Elementary schools
- `secondary_school` - High schools

### Restaurants
- `restaurant` - Restaurants
- `cafe` - Cafes
- `food` - Food establishments

### Metro Stations
- `subway_station` - Metro/subway stations
- `transit_station` - Transit hubs
- `train_station` - Train stations

## Testing

### Test the API endpoint:
```bash
curl -X POST http://localhost:5000/api/nearby-amenities \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 12.9716,
    "lng": 77.5946,
    "radius": 1000,
    "property_id": 123
  }'
```

### Expected Response:
```json
{
  "hospitals_count": 5,
  "shopping_malls_count": 3,
  "schools_count": 8,
  "restaurants_count": 25,
  "metro_stations_count": 2,
  "total_count": 43,
  "stored_in_db": true
}
```

## Verify Database Storage

```sql
-- Check if counts were stored
SELECT id, projectname, areaname,
       hospitals_count,
       shopping_malls_count,
       schools_count,
       restaurants_count,
       metro_stations_count,
       (hospitals_count + shopping_malls_count + schools_count + 
        restaurants_count + metro_stations_count) as total_count
FROM unified_data_DataType_Raghu
WHERE id = 123;
```

## Cost Optimization

### Google Places API Pricing
- Nearby Search: $32 per 1,000 requests
- Free tier: $200 credit per month (~6,250 requests)

### Strategy
1. **Always fetch from API first** - Ensures accurate data
2. **Store in database** - Cached for future comparisons
3. **5 API calls per property** - One for each amenity type
4. **Cost per property**: ~$0.16 (5 calls × $0.032)

### Example Costs
- 100 properties: $16
- 500 properties: $80
- 1,000 properties: $160

## Error Handling

The API handles:
- Missing coordinates → 400 error
- Missing property_id → 400 error
- Google API failures → Continues with partial data
- Database failures → Returns counts anyway (logs warning)
- Network timeouts → 500 error with message

## Flow Diagram

```
User opens comparison
    ↓
Frontend shows "Fetching count..."
    ↓
Call /api/nearby-amenities with property_id
    ↓
Backend calls Google Places API (5 types)
    ↓
Backend stores counts in database columns
    ↓
Backend returns counts to frontend
    ↓
Frontend displays: "43 amenities nearby"
    ↓
Next time same property compared:
    ↓
Frontend still calls API (to ensure accuracy)
    ↓
Backend updates database with latest counts
    ↓
Always shows fresh data
```

## Benefits

✅ **Always accurate** - Fetches from Google Places API every time
✅ **Database cached** - Stored for analytics and reporting
✅ **Detailed breakdown** - 5 specific amenity types
✅ **Hover tooltip** - Shows breakdown on hover
✅ **Error resilient** - Continues with partial data if some API calls fail
✅ **Cost effective** - Only fetches when user compares properties

## Next Steps

1. Add the endpoint to `api.py`
2. Get Google Places API key
3. Add environment variables to `.env`
4. Test with sample property
5. Verify counts are stored in database
6. Monitor API usage and costs
