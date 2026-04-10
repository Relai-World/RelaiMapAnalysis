/**
 * Enhanced Cache Manager for Relai Map Analysis
 * Handles persistent caching for amenities and static assets
 */

class CacheManager {
  constructor() {
    this.CACHE_VERSION = 'v1';
    this.AMENITY_CACHE_KEY = 'relai_amenity_cache';
    this.CACHE_EXPIRY_DAYS = 7; // Cache expires after 7 days
  }

  /**
   * Get cached amenities from localStorage
   * @param {string} cacheKey - Unique key for location+amenity type
   * @returns {Array|null} - Cached amenities or null
   */
  getAmenityCache(cacheKey) {
    try {
      const cache = localStorage.getItem(this.AMENITY_CACHE_KEY);
      if (!cache) return null;

      const parsed = JSON.parse(cache);
      const entry = parsed[cacheKey];

      if (!entry) return null;

      // Check if cache is expired
      const now = Date.now();
      const expiryTime = entry.timestamp + (this.CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000);

      if (now > expiryTime) {
        console.log(`🗑️ Cache expired for ${cacheKey}`);
        this.removeAmenityCache(cacheKey);
        return null;
      }

      console.log(`💾 LocalStorage cache hit for ${cacheKey}`);
      return entry.data;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return null;
    }
  }

  /**
   * Save amenities to localStorage
   * @param {string} cacheKey - Unique key for location+amenity type
   * @param {Array} amenities - Amenities data to cache
   */
  setAmenityCache(cacheKey, amenities) {
    try {
      const cache = localStorage.getItem(this.AMENITY_CACHE_KEY);
      const parsed = cache ? JSON.parse(cache) : {};

      parsed[cacheKey] = {
        data: amenities,
        timestamp: Date.now()
      };

      localStorage.setItem(this.AMENITY_CACHE_KEY, JSON.stringify(parsed));
      console.log(`💾 Saved ${amenities.length} amenities to localStorage for ${cacheKey}`);
    } catch (error) {
      console.error('Error saving to localStorage:', error);
      // If quota exceeded, clear old entries
      if (error.name === 'QuotaExceededError') {
        this.clearOldCaches();
        // Try again
        try {
          const parsed = {};
          parsed[cacheKey] = {
            data: amenities,
            timestamp: Date.now()
          };
          localStorage.setItem(this.AMENITY_CACHE_KEY, JSON.stringify(parsed));
        } catch (e) {
          console.error('Failed to save after clearing:', e);
        }
      }
    }
  }

  /**
   * Remove specific amenity cache
   * @param {string} cacheKey - Cache key to remove
   */
  removeAmenityCache(cacheKey) {
    try {
      const cache = localStorage.getItem(this.AMENITY_CACHE_KEY);
      if (!cache) return;

      const parsed = JSON.parse(cache);
      delete parsed[cacheKey];
      localStorage.setItem(this.AMENITY_CACHE_KEY, JSON.stringify(parsed));
    } catch (error) {
      console.error('Error removing cache:', error);
    }
  }

  /**
   * Clear old cache entries (older than expiry days)
   */
  clearOldCaches() {
    try {
      const cache = localStorage.getItem(this.AMENITY_CACHE_KEY);
      if (!cache) return;

      const parsed = JSON.parse(cache);
      const now = Date.now();
      const expiryMs = this.CACHE_EXPIRY_DAYS * 24 * 60 * 60 * 1000;

      let cleared = 0;
      Object.keys(parsed).forEach(key => {
        if (now - parsed[key].timestamp > expiryMs) {
          delete parsed[key];
          cleared++;
        }
      });

      localStorage.setItem(this.AMENITY_CACHE_KEY, JSON.stringify(parsed));
      console.log(`🗑️ Cleared ${cleared} expired cache entries`);
    } catch (error) {
      console.error('Error clearing old caches:', error);
    }
  }

  /**
   * Clear all amenity caches
   */
  clearAllCaches() {
    try {
      localStorage.removeItem(this.AMENITY_CACHE_KEY);
      console.log('🗑️ Cleared all amenity caches');
    } catch (error) {
      console.error('Error clearing all caches:', error);
    }
  }

  /**
   * Get cache statistics
   * @returns {Object} - Cache stats
   */
  getCacheStats() {
    try {
      const cache = localStorage.getItem(this.AMENITY_CACHE_KEY);
      if (!cache) return { entries: 0, size: 0 };

      const parsed = JSON.parse(cache);
      const entries = Object.keys(parsed).length;
      const size = new Blob([cache]).size;

      return {
        entries,
        size: (size / 1024).toFixed(2) + ' KB',
        sizeBytes: size
      };
    } catch (error) {
      console.error('Error getting cache stats:', error);
      return { entries: 0, size: 0 };
    }
  }
}

// Create global instance
window.cacheManager = new CacheManager();

// Clear old caches on page load
window.addEventListener('load', () => {
  window.cacheManager.clearOldCaches();
});


/**
 * Global cache control functions for debugging
 * Access these from browser console
 */
window.cacheControl = {
  /**
   * Get cache statistics
   */
  stats: () => {
    const stats = window.cacheManager.getCacheStats();
    console.log('📊 Cache Statistics:');
    console.log(`   Entries: ${stats.entries}`);
    console.log(`   Size: ${stats.size}`);
    return stats;
  },

  /**
   * Clear all amenity caches
   */
  clear: () => {
    window.cacheManager.clearAllCaches();
    window._amenityCache = {}; // Clear in-memory cache too
    console.log('✅ All caches cleared (localStorage + in-memory)');
  },

  /**
   * Clear service worker cache
   */
  clearServiceWorker: async () => {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
      console.log('✅ Service Worker cache clear requested');
    } else {
      console.warn('⚠️ No active Service Worker found');
    }
  },

  /**
   * View all cached keys
   */
  list: () => {
    try {
      const cache = localStorage.getItem(window.cacheManager.AMENITY_CACHE_KEY);
      if (!cache) {
        console.log('📭 No cached amenities');
        return [];
      }

      const parsed = JSON.parse(cache);
      const keys = Object.keys(parsed);
      
      console.log(`📋 Cached Amenity Keys (${keys.length}):`);
      keys.forEach((key, index) => {
        const entry = parsed[key];
        const age = Math.floor((Date.now() - entry.timestamp) / (1000 * 60 * 60 * 24));
        console.log(`   ${index + 1}. ${key} (${entry.data.length} items, ${age} days old)`);
      });
      
      return keys;
    } catch (error) {
      console.error('Error listing cache:', error);
      return [];
    }
  },

  /**
   * Remove specific cache entry
   */
  remove: (cacheKey) => {
    window.cacheManager.removeAmenityCache(cacheKey);
    delete window._amenityCache[cacheKey];
    console.log(`✅ Removed cache for: ${cacheKey}`);
  },

  /**
   * Help message
   */
  help: () => {
    console.log(`
🔧 Cache Control Commands:
   cacheControl.stats()              - View cache statistics
   cacheControl.list()               - List all cached keys
   cacheControl.clear()              - Clear all amenity caches
   cacheControl.clearServiceWorker() - Clear service worker cache
   cacheControl.remove(key)          - Remove specific cache entry
   cacheControl.help()               - Show this help message
    `);
  }
};

// Show help on load
console.log('💡 Cache Manager loaded. Type "cacheControl.help()" for available commands.');
