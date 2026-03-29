/**
 * Browser Cache Manager
 * Handles localStorage caching for locations and amenities
 */

const CacheManager = {
  // Cache durations
  DURATIONS: {
    LOCATIONS: 24 * 60 * 60 * 1000,  // 24 hours
    AMENITIES: 7 * 24 * 60 * 60 * 1000,  // 7 days (amenities don't change often)
    PROPERTIES: 6 * 60 * 60 * 1000   // 6 hours (properties update more frequently)
  },

  /**
   * Get cached data
   * @param {string} key - Cache key
   * @param {number} maxAge - Maximum age in milliseconds
   * @returns {any|null} Cached data or null if expired/missing
   */
  get(key, maxAge) {
    try {
      const cached = localStorage.getItem(key);
      if (!cached) return null;

      const { data, timestamp } = JSON.parse(cached);
      const age = Date.now() - timestamp;

      if (age > maxAge) {
        console.log(`🗑️ Cache expired for ${key} (age: ${Math.round(age / 1000 / 60)} min)`);
        localStorage.removeItem(key);
        return null;
      }

      console.log(`✅ Cache hit for ${key} (age: ${Math.round(age / 1000 / 60)} min)`);
      return data;
    } catch (e) {
      console.error(`❌ Cache read error for ${key}:`, e);
      return null;
    }
  },

  /**
   * Set cached data
   * @param {string} key - Cache key
   * @param {any} data - Data to cache
   */
  set(key, data) {
    try {
      localStorage.setItem(key, JSON.stringify({
        data: data,
        timestamp: Date.now()
      }));
      console.log(`💾 Cached ${key}`);
    } catch (e) {
      console.error(`❌ Cache write error for ${key}:`, e);
      // If quota exceeded, clear old caches
      if (e.name === 'QuotaExceededError') {
        this.clearOldCaches();
        // Try again
        try {
          localStorage.setItem(key, JSON.stringify({
            data: data,
            timestamp: Date.now()
          }));
        } catch (e2) {
          console.error('❌ Still failed after clearing old caches');
        }
      }
    }
  },

  /**
   * Clear specific cache
   * @param {string} key - Cache key to clear
   */
  clear(key) {
    localStorage.removeItem(key);
    console.log(`🗑️ Cleared cache: ${key}`);
  },

  /**
   * Clear all app caches
   */
  clearAll() {
    const keys = Object.keys(localStorage);
    const appKeys = keys.filter(k => 
      k.startsWith('hyderabad_') || 
      k.startsWith('amenity_') ||
      k.startsWith('property_')
    );
    
    appKeys.forEach(key => localStorage.removeItem(key));
    console.log(`🗑️ Cleared ${appKeys.length} cache entries`);
  },

  /**
   * Clear caches older than their max age
   */
  clearOldCaches() {
    const keys = Object.keys(localStorage);
    let cleared = 0;

    keys.forEach(key => {
      try {
        const cached = localStorage.getItem(key);
        if (!cached) return;

        const { timestamp } = JSON.parse(cached);
        const age = Date.now() - timestamp;

        // Clear if older than 30 days
        if (age > 30 * 24 * 60 * 60 * 1000) {
          localStorage.removeItem(key);
          cleared++;
        }
      } catch (e) {
        // Invalid cache entry, remove it
        localStorage.removeItem(key);
        cleared++;
      }
    });

    if (cleared > 0) {
      console.log(`🗑️ Cleared ${cleared} old cache entries`);
    }
  },

  /**
   * Get cache statistics
   * @returns {object} Cache stats
   */
  getStats() {
    const keys = Object.keys(localStorage);
    const appKeys = keys.filter(k => 
      k.startsWith('hyderabad_') || 
      k.startsWith('amenity_') ||
      k.startsWith('property_')
    );

    let totalSize = 0;
    const entries = [];

    appKeys.forEach(key => {
      try {
        const value = localStorage.getItem(key);
        const size = new Blob([value]).size;
        totalSize += size;

        const { timestamp } = JSON.parse(value);
        const age = Date.now() - timestamp;

        entries.push({
          key,
          size: (size / 1024).toFixed(2) + ' KB',
          age: Math.round(age / 1000 / 60) + ' min'
        });
      } catch (e) {
        // Skip invalid entries
      }
    });

    return {
      totalEntries: appKeys.length,
      totalSize: (totalSize / 1024).toFixed(2) + ' KB',
      entries: entries
    };
  }
};

// Expose globally
window.CacheManager = CacheManager;

// Clear old caches on load
CacheManager.clearOldCaches();

console.log('💾 Cache Manager initialized');
