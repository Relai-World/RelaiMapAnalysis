# Quick Start: City-Based Layers

## What Changed

Your app now automatically shows different layers based on whether you're viewing Hyderabad or Bangalore!

## Hyderabad Layers (Unchanged)
- Highways
- Metro
- ORR (Outer Ring Road)
- Lakes
- RRR (Regional Ring Road)
- HMDA (Boundary)
- Plan 2031
- Floods

## Bangalore Layers (New!)
- Highways
- Metro (Namma Metro)
- ORR
- Lakes
- PRR (Peripheral Ring Road)
- BBMP (Boundary)
- Floods

## How to Test

### 1. View Hyderabad
```
Open app → Should show Hyderabad layers by default
```

### 2. View Bangalore
```
Pan map to Bangalore → Layers automatically switch to Bangalore
```

### 3. Switch Between Cities
```
Pan between cities → Watch layers update automatically
```

## Console Commands

Check current city:
```javascript
window.currentCity  // Returns 'hyderabad' or 'bangalore'
```

Manually detect city:
```javascript
detectCity(map)  // Returns current city based on map center
```

## Files Modified

1. `frontend/city-layers.js` - NEW: City detection system
2. `frontend/app.js` - Added Bangalore layers
3. `frontend/index.html` - Added city-layers script

## Important

✅ Hyderabad layers work exactly as before
✅ No breaking changes
✅ Automatic city detection
✅ Smooth layer switching

## Need Help?

Check browser console for messages:
- `🌆 Detected city: [city name]`
- `✅ Layer controls updated for [city name]`
- `🌆 City changed: [old] → [new]`
