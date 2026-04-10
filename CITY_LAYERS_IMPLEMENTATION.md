# City-Based Layer System Implementation

## Overview

Implemented a dynamic city-based layer system that automatically detects whether the user is viewing Hyderabad or Bangalore and shows the appropriate layers for each city.

## What Was Done

### 1. Created City Layer Manager (`frontend/city-layers.js`)
- Detects current city based on map center coordinates
- Dynamically updates layer controls based on detected city
- Monitors map movement to detect city changes
- Maintains separate layer configurations for each city

### 2. Added Bangalore Layers (`frontend/app.js`)
All Bangalore layers added with "blr-" prefix to avoid conflicts with Hyderabad layers:

- `blr-highways-layer` - Major highways and arterial roads
- `blr-metro-layer` - Bangalore Metro (Namma Metro)
- `blr-orr-layer` - Outer Ring Road
- `blr-lakes-layer` - Lakes and water bodies
- `blr-prr-layer` - Peripheral Ring Road (PRR)
- `blr-bbmp-layer` - BBMP Boundary
- `blr-floods-layer` - Flood prone areas

### 3. Data Files Used
Bangalore data files (already present in `frontend/data/`):
- `bangalore_bbmp.geojson` - BBMP boundary
- `bangalore_floods.geojson` - Flood data
- `bangalore_lakes.geojson` - Lakes
- `bangalore_metro.geojson` - Metro lines
- `banglore_highways.geojson` - Highways
- `PRR.geojson` - Peripheral Ring Road (used for both ORR and PRR)

### 4. Updated Layer Toggle System
- Wrapped layer toggle event listeners in `attachLayerToggles()` function
- Made function globally available for dynamic re-attachment
- Added opacity settings for all Bangalore layers
- Special handling for Bangalore metro and floods layers

### 5. Updated HTML (`frontend/index.html`)
- Added `city-layers.js` script
- Layer controls now dynamically generated based on city

## City Configurations

### Hyderabad Layers
1. Highways - Major highways & arterial roads
2. Metro - Hyderabad Metro corridors
3. ORR - Outer Ring Road
4. Lakes - Lakes & water bodies
5. RRR - Regional Ring Road
6. HMDA - HMDA Masterplan boundary
7. Plan 2031 - HMDA Master Plan 2031
8. Floods - Drainage networks & flood risk

### Bangalore Layers
1. Highways - Major highways & arterial roads
2. Metro - Bangalore Metro (Namma Metro)
3. ORR - Outer Ring Road
4. Lakes - Lakes & water bodies
5. PRR - Peripheral Ring Road
6. BBMP - BBMP Boundary
7. Floods - Flood prone areas

## How It Works

### City Detection
```javascript
// Hyderabad bounds: [77.8, 17.0] to [79.0, 17.9]
// Bangalore bounds: [77.3, 12.7] to [77.9, 13.2]

// Detects city based on map center coordinates
const city = detectCity(map);
```

### Dynamic Layer Updates
1. User pans map to different city
2. System detects city change
3. Layer controls automatically update
4. Only relevant city layers are shown
5. Event listeners re-attached

### Layer Naming Convention
- Hyderabad layers: `{name}-layer` (e.g., `highways-layer`)
- Bangalore layers: `blr-{name}-layer` (e.g., `blr-highways-layer`)

## Key Features

### 1. Automatic City Detection
- Detects city based on map viewport center
- Updates layers when user pans to different city
- Smooth transition between cities

### 2. No Conflicts
- Hyderabad and Bangalore layers coexist
- Separate layer IDs prevent conflicts
- Both cities' data loaded simultaneously

### 3. Preserved Hyderabad Logic
- All Hyderabad layer logic unchanged
- Original functionality maintained
- No breaking changes to existing features

### 4. Consistent UI
- Same layer control design for both cities
- Same icons and styling
- Seamless user experience

## Testing

### Test Hyderabad Layers
1. Open the app
2. Map should center on Hyderabad (78.38, 17.44)
3. Layer controls should show Hyderabad layers
4. Toggle layers to verify they work

### Test Bangalore Layers
1. Pan map to Bangalore (77.59, 12.97)
2. Layer controls should automatically update
3. Should show Bangalore-specific layers
4. Toggle layers to verify they work

### Test City Switching
1. Start in Hyderabad
2. Pan to Bangalore
3. Watch console for city change message
4. Verify layer controls update automatically
5. Pan back to Hyderabad
6. Verify it switches back

## Console Messages

Watch for these messages in browser console:

```
🌆 Detected city: Hyderabad
✅ Layer controls updated for Hyderabad
✅ Bangalore layers added successfully

// When switching cities:
🌆 City changed: Hyderabad → Bangalore
✅ Layer controls updated for Bangalore
```

## File Structure

```
frontend/
├── city-layers.js          # City detection and layer management
├── app.js                  # Updated with Bangalore layers
├── index.html              # Updated with city-layers script
└── data/
    ├── bangalore_bbmp.geojson
    ├── bangalore_floods.geojson
    ├── bangalore_lakes.geojson
    ├── bangalore_metro.geojson
    ├── banglore_highways.geojson
    └── PRR.geojson
```

## Configuration

### Add More Cities
Edit `frontend/city-layers.js`:

```javascript
const CITY_BOUNDS = {
  hyderabad: { ... },
  bangalore: { ... },
  mumbai: {  // Add new city
    center: [72.88, 19.08],
    bounds: [[72.7, 18.9], [73.0, 19.3]],
    name: 'Mumbai'
  }
};

const CITY_LAYERS = {
  mumbai: {
    layers: [
      // Define Mumbai layers
    ]
  }
};
```

### Customize Layer Order
Edit the `layers` array in `CITY_LAYERS` configuration to change the order of layer controls.

### Change City Bounds
Adjust the `bounds` array in `CITY_BOUNDS` to fine-tune city detection areas.

## Important Notes

1. **Hyderabad Logic Preserved**: All original Hyderabad layer logic remains unchanged
2. **No Breaking Changes**: Existing functionality continues to work as before
3. **Extensible**: Easy to add more cities using the same pattern
4. **Performance**: All layers loaded once, only controls update dynamically
5. **Data Files**: Ensure all Bangalore data files are present in `frontend/data/`

## Troubleshooting

### Layers Not Showing
- Check browser console for errors
- Verify data files exist in `frontend/data/`
- Check layer IDs match in `city-layers.js` and `app.js`

### City Not Detecting
- Check map center coordinates in console
- Verify city bounds in `CITY_BOUNDS`
- Adjust bounds if needed

### Layer Toggles Not Working
- Check if `attachLayerToggles()` is being called
- Verify layer IDs in HTML match layer IDs in map
- Check console for layer not found errors

## Next Steps

1. Test both cities thoroughly
2. Verify all layer toggles work correctly
3. Check layer opacity settings
4. Test city switching multiple times
5. Verify no console errors

## Summary

Successfully implemented a city-based layer system that:
- ✅ Keeps Hyderabad layers unchanged
- ✅ Adds Bangalore layers with separate IDs
- ✅ Automatically detects current city
- ✅ Dynamically updates layer controls
- ✅ Maintains consistent UI/UX
- ✅ No breaking changes to existing code
