# Caching System Documentation

## Overview

The Relai Map Analysis application now includes a comprehensive multi-layer caching system to improve performance and reduce latency for location amenities and static assets like the Plan 2031 layer.

## Cache Layers

### 1. In-Memory Cache (Fastest)
- **Location**: JavaScript runtime memory
- **Lifetime**: Current browser session only
- **Speed**: Instant (< 1ms)
- **Use Case**: Repeated queries within the same session

### 2. LocalStorage Cache (Persistent)
- **Location**: Browser localStorage
- **Lifetime**: 7 days (configurable)
- **Speed**: Very fast (< 10ms)
- **Use Case**: Amenity data across browser sessions
- **Size Limit**: ~5-10MB (browser dependent)

### 3. Supabase Database Cache
- **Location**: Remote database
- **Lifetime**: Permanent until manually cleared
- **Speed**: Fast (100-500ms depending on network)
- **Use Case**: Shared cache across all users

### 4. Service Worker Cache (Static Assets)
- **Location**: Browser cache storage
- **Lifetime**: Until cache version changes
- **Speed**: Very fast (< 50ms)
- **Use Case**: Plan 2031 image and other static assets

## Cache Flow for Amenities

```
User requests amenities
    ↓
1. Check in-memory cache → Found? Return immediately
    ↓ (Not found)
2. Check localStorage → Found? Return + promote to in-memory
    ↓ (Not found)
3. Check Supabase DB → Found? Return + save to localStorage + in-memory
    ↓ (Not found)
4. Fetch from Overpass API → Save to all cache layers
```

## Cache Management

### Browser Console Commands

Access cache control from the browser console:

```javascript
// View cache statistics
cacheControl.stats()

// List all cached amenity keys
cacheControl.list()

// Clear all amenity caches
cacheControl.clear()

// Clear service worker cache (Plan 2031 image, etc.)
cacheControl.clearServiceWorker()

// Remove specific cache entry
cacheControl.remove('location_123_schools')

// Show help
cacheControl.help()
```

### Automatic Cache Management

- **Expiry**: LocalStorage cache automatically expires after 7 days
- **Cleanup**: Old cache entries are automatically removed on page load
- **Quota Management**: If localStorage quota is exceeded, old entries are cleared automatically

## Configuration

### Cache Expiry Time

Edit `frontend/cache-manager.js`:

```javascript
this.CACHE_EXPIRY_DAYS = 7; // Change to desired number of days
```

### Service Worker Cache Version

Edit `frontend/service-worker.js`:

```javascript
const CACHE_NAME = 'relai-map-cache-v1'; // Increment version to force cache refresh
```

### Add More Static Assets to Cache

Edit `frontend/service-worker.js`:

```javascript
const STATIC_ASSETS = [
  '/data/hmda_test_300dpi.png',
  '/data/hmda_masterplan.png',
  '/data/your-new-asset.png', // Add your asset here
];
```

## Benefits

1. **Reduced Latency**: Amenities load instantly from cache instead of waiting for API calls
2. **Offline Support**: Cached data available even with poor network connectivity
3. **Reduced API Costs**: Fewer calls to Google Places API and Overpass API
4. **Better User Experience**: Faster page loads and smoother interactions
5. **Bandwidth Savings**: Large images like Plan 2031 are cached and served locally

## Monitoring

### Check Cache Performance

Open browser DevTools Console and look for cache-related logs:

- `⚡ In-memory cache hit` - Fastest, data from current session
- `💾 LocalStorage cache hit` - Fast, data from previous session
- `✅ DB cache hit` - Moderate, data from database
- `🌐 No cache — fetching from API` - Slowest, fresh data from API

### View Cache Size

```javascript
cacheControl.stats()
// Output:
// 📊 Cache Statistics:
//    Entries: 15
//    Size: 234.56 KB
```

## Troubleshooting

### Cache Not Working

1. Check if localStorage is enabled in browser
2. Check browser console for errors
3. Verify service worker is registered: `navigator.serviceWorker.controller`

### Clear All Caches

```javascript
// Clear amenity caches
cacheControl.clear()

// Clear service worker cache
cacheControl.clearServiceWorker()

// Hard refresh browser
// Windows/Linux: Ctrl + Shift + R
// Mac: Cmd + Shift + R
```

### Cache Taking Too Much Space

```javascript
// Check current size
cacheControl.stats()

// Clear old entries
cacheControl.clear()
```

## Technical Details

### Cache Keys Format

Amenity cache keys follow this pattern:
```
location_{locationId}_{amenityType}
```

Example: `location_123_schools`

### Storage Locations

- **In-memory**: `window._amenityCache` object
- **LocalStorage**: `relai_amenity_cache` key
- **Service Worker**: `relai-map-cache-v1` cache storage

## Future Enhancements

- [ ] Add cache preloading for popular locations
- [ ] Implement cache warming on idle
- [ ] Add cache compression for larger datasets
- [ ] Implement IndexedDB for larger storage capacity
- [ ] Add cache analytics and reporting
