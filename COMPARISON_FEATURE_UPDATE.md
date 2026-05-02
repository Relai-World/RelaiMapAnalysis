# Property Comparison Feature - Field Structure Update

## Summary
Updated the property comparison feature to display the specific fields requested by the user, with proper data access patterns and Google Places API fallback for amenities.

## Changes Made

### 1. Mobile Card Rendering (`renderMobileCards`)
**Updated sections to match new field requirements:**

#### Pricing Section
- Price / sqft
- Base Price

#### Project Information Section (NEW)
- Project Name
- Builder Name
- RERA Number
- Project Type
- Community Type
- Construction Status
- Launch Date
- Possession Date
- Total Land Area

#### Unit Specifications Section
- Area (sqft)
- Power Backup
- Visitor Parking

#### Location & Ratings Section
- Area Name
- Google Rating
- Grid Score (calculated from location insights)

#### Amenities Section
- Nearby Amenities (with Google Places API fallback)

**Removed old sections:**
- ❌ Generic "Specifications" section (Carpet Area, Floor Height, Parking, Facing)
- ❌ "Builder Track Record" section (Builder Age, Completed/Ongoing/Total Projects)

### 2. Desktop Table Rendering
Already had the correct field structure from previous update.

### 3. PDF Export (`exportToPDF`)
**Updated sections:**
- ✅ Pricing: Price/sqft, Base Price
- ✅ Project Information: All 9 fields (Project Name, Builder Name, RERA, etc.)
- ✅ Unit Specifications: Area, Power Backup, Visitor Parking
- ✅ Location & Ratings: Area Name, Google Rating, Grid Score
- ✅ Amenities: Nearby Amenities (from table data)

**Removed sections:**
- ❌ Old "Specifications" section (Carpet Area, Floor Height, Parking, Facing)
- ❌ "Builder Track Record" section

### 4. CSV Export (`exportToCSV`)
**Updated sections to match PDF export:**
- ✅ Pricing
- ✅ Project Information
- ✅ Unit Specifications
- ✅ Location & Ratings
- ✅ Amenities

### 5. Google Places API Integration
**Added amenities fallback logic:**
- First checks `external_amenities` field in property data
- If empty/null, displays "Loading..." placeholder
- Calls `fetchAmenitiesFromGoogle()` after rendering (both desktop and mobile)
- Parses coordinates from multiple formats:
  - JSON object: `{"lat": x, "lng": y}`
  - Comma-separated: `"x,y"`
  - Object: `{lat: x, lng: y}`

**Note:** The Google Places API call is currently a placeholder. In production, you'll need to:
1. Create an API endpoint in `api.py` that accepts lat/lng
2. Call Google Places API Nearby Search
3. Return amenities list
4. Update the placeholder text with actual amenities

## Data Access Pattern
All fields now use the correct pattern to check both top-level and `full_details`:
```javascript
const value = p.field || p.full_details?.field;
```

This ensures data is found regardless of where it's stored in the property object.

## Grid Score Calculation
Grid Score is calculated from location insights:
```javascript
const avgScore = (
  (connectivity_score || 0) + 
  (amenities_score || 0) + 
  ((growth_score || 0) * 10) + 
  ((investment_score || 0) * 10)
) / 4;
```

## Testing Checklist
- [ ] Desktop comparison table shows all new fields
- [ ] Mobile comparison cards show all new fields
- [ ] PDF export includes all new fields
- [ ] CSV export includes all new fields
- [ ] Amenities show from table when available
- [ ] Amenities show "Loading..." when not in table
- [ ] Grid Score calculates correctly from location insights
- [ ] All fields handle null/undefined values gracefully
- [ ] Fields check both top-level and full_details object

## Next Steps
1. **Implement Google Places API endpoint** in `api.py`:
   ```python
   @app.route('/api/nearby-amenities', methods=['POST'])
   def get_nearby_amenities():
       data = request.json
       lat = data.get('lat')
       lng = data.get('lng')
       # Call Google Places API
       # Return amenities list
   ```

2. **Update `fetchAmenitiesFromGoogle()` in comparison-ui.js** to call the API:
   ```javascript
   const response = await fetch('/api/nearby-amenities', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ lat, lng })
   });
   const amenities = await response.json();
   ```

3. **Test with real property data** to verify all fields display correctly

## Files Modified
- `frontend/comparison-ui.js` - Updated mobile cards, PDF export, CSV export, and amenities logic
