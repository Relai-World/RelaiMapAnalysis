# Testing Amenities Count Display

## Quick Test Guide

### Test 1: Properties with Stored Amenities
**Expected:** Should show count immediately (e.g., "**15** amenities nearby")

1. Open the map application
2. Add 2-3 properties to comparison that have `external_amenities` data
3. Click "Show Comparison" button
4. **Desktop:** Check the "Nearby Amenities" row shows counts
5. **Mobile:** Swipe through cards and check "🏊 Amenities" section shows counts

### Test 2: Properties without Stored Amenities
**Expected:** Should show "Fetching count..." then call API

1. Add properties without `external_amenities` data
2. Click "Show Comparison" button
3. Should see "Fetching count..." text
4. **If API is implemented:** Count should appear after API call
5. **If API not implemented:** Will show error message

### Test 3: Mixed Properties
**Expected:** Some show count immediately, others fetch from API

1. Add mix of properties (some with amenities, some without)
2. Click "Show Comparison" button
3. Properties with data show count immediately
4. Properties without data show "Fetching count..."

### Test 4: Error Handling
**Expected:** Graceful error messages

Test these scenarios:
- Property without coordinates → "Location unavailable"
- API endpoint not available → "Unable to fetch"
- API returns no results → "No amenities found"

## Visual Verification

### Desktop Table
```
┌──────────────────────┬──────────────────┬──────────────────┐
│ Attribute            │ Property 1       │ Property 2       │
├──────────────────────┼──────────────────┼──────────────────┤
│ 🏊 Amenities                                                │
├──────────────────────┼──────────────────┼──────────────────┤
│ Nearby Amenities     │ 23 amenities     │ 15 amenities     │
│                      │ nearby           │ nearby           │
└──────────────────────┴──────────────────┴──────────────────┘
```

### Mobile Card
```
┌─────────────────────────────────────┐
│ 🏊 Amenities                        │
│ ─────────────────────────────────── │
│ Nearby Amenities: 23 amenities      │
│                   nearby            │
└─────────────────────────────────────┘
```

## Browser Console Checks

Open browser console (F12) and check for:

✅ **Success:**
```
✅ Fetched amenities count: 15
```

❌ **Errors:**
```
❌ Amenities API error: HTTP 404
❌ Failed to parse location: ...
```

## Sample Properties to Test

### Properties with Amenities (should show count immediately)
- Check `unified_data_DataType_Raghu` table
- Filter: `external_amenities IS NOT NULL AND external_amenities != ''`
- Example: Properties in popular areas like Whitefield, Koramangala

### Properties without Amenities (should fetch from API)
- Filter: `external_amenities IS NULL OR external_amenities = ''`
- Must have `google_place_location` for API to work

## SQL Query to Find Test Properties

```sql
-- Properties WITH amenities
SELECT id, projectname, areaname, 
       LENGTH(external_amenities) - LENGTH(REPLACE(external_amenities, ',', '')) + 1 as amenity_count
FROM unified_data_DataType_Raghu
WHERE external_amenities IS NOT NULL 
  AND external_amenities != ''
ORDER BY amenity_count DESC
LIMIT 5;

-- Properties WITHOUT amenities but WITH coordinates
SELECT id, projectname, areaname, google_place_location
FROM unified_data_DataType_Raghu
WHERE (external_amenities IS NULL OR external_amenities = '')
  AND google_place_location IS NOT NULL
LIMIT 5;
```

## Backend API Testing

If you've implemented the `/api/nearby-amenities` endpoint:

```bash
# Test with sample coordinates (Bangalore)
curl -X POST http://localhost:5000/api/nearby-amenities \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lng": 77.5946, "radius": 1000}'

# Expected response:
{
  "amenities": ["School", "Hospital", "Shopping Mall", ...],
  "count": 15
}
```

## Troubleshooting

### Issue: Shows "Fetching count..." forever
**Cause:** API endpoint not implemented or not responding
**Fix:** Implement `/api/nearby-amenities` endpoint (see `GOOGLE_PLACES_API_IMPLEMENTATION.md`)

### Issue: Shows "Location unavailable"
**Cause:** Property missing `google_place_location` field
**Fix:** Use properties with coordinates, or add coordinates to database

### Issue: Count doesn't match expected
**Cause:** Counting comma-separated items, may include empty strings
**Fix:** Already handled with `.filter(Boolean)` in code

### Issue: Bold text not showing
**Cause:** CSS not loading or `<strong>` tag not rendering
**Fix:** Check browser console for CSS errors, verify HTML rendering

## Success Criteria

✅ Desktop table shows amenities count (not names)
✅ Mobile cards show amenities count (not names)
✅ Count is bold and easy to read
✅ Loading states are clear ("Fetching count...")
✅ Error messages are user-friendly
✅ API integration works when endpoint is available
✅ No console errors
✅ Comparison still works with 2+ properties

## Next Steps After Testing

1. If tests pass → Mark task as complete
2. If API needed → Implement backend endpoint
3. If styling issues → Update CSS
4. If data issues → Update database queries

## Files to Check

- `frontend/comparison-ui.js` (v2.6)
- `frontend/index.html` (script version 2.6)
- `frontend/style.css` (for bold text styling)
- `api.py` (for backend endpoint)
- `.env` (for Google Places API key)
