/**
 * ComparisonManager - Manages property comparison state and data fetching
 * 
 * Responsibilities:
 * - Manage comparison state (add/remove properties)
 * - Persist state to localStorage
 * - Fetch property and location data
 * - Provide state to UI components
 * - Track analytics events
 */

class ComparisonManager {
  constructor() {
    // Check if callSupabaseRPC is available (warning only, don't throw)
    if (typeof callSupabaseRPC === 'undefined') {
      console.warn('⚠️ WARNING: callSupabaseRPC is not defined yet!');
      console.warn('💡 Make sure app.js is loaded BEFORE comparison-manager.js');
      console.warn('💡 This may cause issues when fetching property data');
    }
    
    this.state = {
      propertyIds: [],
      timestamp: Date.now(),
      version: "1.0"
    };
    
    // Cache for fetched property data to avoid redundant API calls
    this.cache = new Map();
    
    // Cache for location insights
    this.locationCache = new Map();
    
    // Observers for UI updates
    this.observers = [];
    
    // Constants
    this.MAX_PROPERTIES = 4;
    this.STORAGE_KEY = 'relai_comparison_state';
    this.ANALYTICS_KEY = 'relai_comparison_analytics';
    this.MAX_ANALYTICS_EVENTS = 100;
    
    // Load saved state from localStorage
    this.loadState();
  }
  
  /* ===============================
     STATE MANAGEMENT
  =============================== */
  
  /**
   * Add a property to comparison
   * @param {number} propertyId - The property ID to add
   * @returns {boolean} - Success status
   */
  addProperty(propertyId) {
    // Check if already in state
    if (this.hasProperty(propertyId)) {
      console.log(`Property ${propertyId} already in comparison`);
      return false;
    }
    
    // Check if limit reached
    if (this.state.propertyIds.length >= this.MAX_PROPERTIES) {
      this.showNotification(`Maximum ${this.MAX_PROPERTIES} properties can be compared`, 'warning');
      return false;
    }
    
    // Add to state
    this.state.propertyIds.push(propertyId);
    this.state.timestamp = Date.now();
    
    // Save to localStorage
    this.saveState();
    
    // Track analytics
    this.trackEvent('comparison_property_added', { propertyId });
    
    // Notify observers
    this.notify();
    
    console.log(`✅ Added property ${propertyId} to comparison. Total: ${this.state.propertyIds.length}`);
    return true;
  }
  
  /**
   * Remove a property from comparison
   * @param {number} propertyId - The property ID to remove
   * @returns {boolean} - Success status
   */
  removeProperty(propertyId) {
    const index = this.state.propertyIds.indexOf(propertyId);
    
    if (index === -1) {
      console.log(`Property ${propertyId} not in comparison`);
      return false;
    }
    
    // Remove from state
    this.state.propertyIds.splice(index, 1);
    this.state.timestamp = Date.now();
    
    // Remove from cache
    this.cache.delete(propertyId);
    
    // Save to localStorage
    this.saveState();
    
    // Track analytics
    this.trackEvent('comparison_property_removed', { propertyId });
    
    // Notify observers
    this.notify();
    
    console.log(`✅ Removed property ${propertyId} from comparison. Total: ${this.state.propertyIds.length}`);
    return true;
  }
  
  /**
   * Check if a property is in comparison
   * @param {number} propertyId - The property ID to check
   * @returns {boolean}
   */
  hasProperty(propertyId) {
    return this.state.propertyIds.includes(propertyId);
  }
  
  /**
   * Get the number of properties in comparison
   * @returns {number}
   */
  getPropertyCount() {
    return this.state.propertyIds.length;
  }
  
  /**
   * Get all property IDs in comparison
   * @returns {number[]}
   */
  getPropertyIds() {
    return [...this.state.propertyIds];
  }
  
  /**
   * Clear all properties from comparison
   */
  clearAll() {
    this.state.propertyIds = [];
    this.state.timestamp = Date.now();
    this.cache.clear();
    this.locationCache.clear();
    this.saveState();
    this.notify();
    console.log('✅ Cleared all properties from comparison');
  }
  
  /* ===============================
     DATA FETCHING
  =============================== */
  
  /**
   * Fetch full property details by ID
   * @param {number} propertyId - The property ID
   * @returns {Promise<Object>} - Property data
   */
  async fetchPropertyDetails(propertyId) {
    // Check cache first
    if (this.cache.has(propertyId)) {
      console.log(`📦 Using cached data for property ${propertyId}`);
      return this.cache.get(propertyId);
    }
    
    console.log(`🔍 Fetching property ${propertyId} from Supabase...`);
    
    try {
      // Use existing callSupabaseRPC function from app.js
      const data = await callSupabaseRPC('get_property_by_id_func', { prop_id: propertyId });
      
      // Handle Supabase RPC response format (returns array)
      const property = Array.isArray(data) && data.length > 0 ? data[0] : data;
      
      if (!property || !property.id) {
        throw new Error(`Property ${propertyId} not found`);
      }
      
      // Store in cache
      this.cache.set(propertyId, property);
      
      console.log(`✅ Fetched property ${propertyId}: ${property.projectname}`);
      return property;
      
    } catch (error) {
      console.error(`❌ Failed to fetch property ${propertyId}:`, error);
      throw error;
    }
  }
  
  /**
   * Fetch location insights for a given area
   * @param {string} areaName - The area/location name
   * @param {string} city - The city (Hyderabad or Bangalore)
   * @returns {Promise<Object|null>} - Location insights or null if not found
   */
  async fetchLocationInsights(areaName, city) {
    if (!areaName) return null;
    
    const cacheKey = `${city}_${areaName}`.toLowerCase();
    
    // Check cache first
    if (this.locationCache.has(cacheKey)) {
      console.log(`📦 Using cached location insights for ${areaName}`);
      return this.locationCache.get(cacheKey);
    }
    
    console.log(`🔍 Fetching location insights for ${areaName}, ${city}...`);
    
    try {
      // Fetch all insights and filter by location name
      // This uses the existing get_all_insights RPC function
      const allInsights = await callSupabaseRPC('get_all_insights');
      
      // Find matching location (case-insensitive)
      const locationInsights = allInsights.find(loc => 
        loc.location && loc.location.toLowerCase() === areaName.toLowerCase()
      );
      
      if (locationInsights) {
        // Store in cache
        this.locationCache.set(cacheKey, locationInsights);
        console.log(`✅ Found location insights for ${areaName}`);
        return locationInsights;
      } else {
        console.log(`⚠️ No location insights found for ${areaName}`);
        return null;
      }
      
    } catch (error) {
      console.error(`❌ Failed to fetch location insights for ${areaName}:`, error);
      return null;
    }
  }
  
  /**
   * Fetch all comparison data (properties + location insights)
   * @returns {Promise<Object>} - { properties: [], locationInsights: Map }
   */
  async fetchAllComparisonData() {
    console.log(`🔄 Fetching comparison data for ${this.state.propertyIds.length} properties...`);
    
    try {
      // Fetch all property details in parallel
      const propertyPromises = this.state.propertyIds.map(id => 
        this.fetchPropertyDetails(id).catch(err => {
          console.error(`Failed to fetch property ${id}:`, err);
          return null; // Return null for failed fetches
        })
      );
      
      const properties = await Promise.all(propertyPromises);
      
      // Filter out null values (failed fetches)
      const validProperties = properties.filter(p => p !== null);
      
      // Extract unique locations
      const uniqueLocations = new Map();
      validProperties.forEach(prop => {
        if (prop.areaname && prop.city) {
          const key = `${prop.city}_${prop.areaname}`.toLowerCase();
          if (!uniqueLocations.has(key)) {
            uniqueLocations.set(key, { areaName: prop.areaname, city: prop.city });
          }
        }
      });
      
      // Fetch location insights in parallel
      const locationPromises = Array.from(uniqueLocations.values()).map(({ areaName, city }) =>
        this.fetchLocationInsights(areaName, city).catch(err => {
          console.error(`Failed to fetch location insights for ${areaName}:`, err);
          return null;
        })
      );
      
      const locationInsightsArray = await Promise.all(locationPromises);
      
      // Create a map of location insights by area name
      const locationInsights = new Map();
      locationInsightsArray.forEach(insights => {
        if (insights && insights.location) {
          locationInsights.set(insights.location.toLowerCase(), insights);
        }
      });
      
      console.log(`✅ Fetched ${validProperties.length} properties and ${locationInsights.size} location insights`);
      
      return {
        properties: validProperties,
        locationInsights
      };
      
    } catch (error) {
      console.error('❌ Failed to fetch comparison data:', error);
      throw error;
    }
  }
  
  /* ===============================
     PERSISTENCE
  =============================== */
  
  /**
   * Load state from localStorage
   */
  loadState() {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      
      if (saved) {
        const parsed = JSON.parse(saved);
        
        // Validate structure
        if (parsed.propertyIds && Array.isArray(parsed.propertyIds)) {
          this.state = {
            propertyIds: parsed.propertyIds,
            timestamp: parsed.timestamp || Date.now(),
            version: parsed.version || "1.0"
          };
          
          console.log(`✅ Loaded comparison state: ${this.state.propertyIds.length} properties`);
        }
      }
    } catch (error) {
      console.error('❌ Failed to load comparison state:', error);
      // Reset to default state
      this.state = {
        propertyIds: [],
        timestamp: Date.now(),
        version: "1.0"
      };
    }
  }
  
  /**
   * Save state to localStorage
   */
  saveState() {
    try {
      const serialized = JSON.stringify(this.state);
      localStorage.setItem(this.STORAGE_KEY, serialized);
      console.log('💾 Saved comparison state to localStorage');
      return true;
    } catch (error) {
      if (error.name === 'QuotaExceededError') {
        console.warn('⚠️ localStorage quota exceeded');
        
        // Try to clear old analytics data and retry
        try {
          localStorage.removeItem(this.ANALYTICS_KEY);
          localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state));
          console.log('💾 Saved comparison state after clearing analytics');
          return true;
        } catch (retryError) {
          console.error('❌ Failed to save comparison state even after cleanup');
          this.showNotification('Unable to save comparison state - storage full', 'error');
          return false;
        }
      } else {
        console.error('❌ Failed to save comparison state:', error);
        this.showNotification('Unable to save comparison state', 'error');
        return false;
      }
    }
  }
  
  /* ===============================
     ANALYTICS
  =============================== */
  
  /**
   * Track an analytics event
   * @param {string} eventName - The event name
   * @param {Object} data - Event data
   */
  trackEvent(eventName, data = {}) {
    try {
      // Load existing events
      const saved = localStorage.getItem(this.ANALYTICS_KEY);
      let events = saved ? JSON.parse(saved) : [];
      
      // Add new event
      events.push({
        event: eventName,
        data,
        timestamp: Date.now()
      });
      
      // Keep only the most recent MAX_ANALYTICS_EVENTS
      if (events.length > this.MAX_ANALYTICS_EVENTS) {
        events = events.slice(-this.MAX_ANALYTICS_EVENTS);
      }
      
      // Save back to localStorage
      localStorage.setItem(this.ANALYTICS_KEY, JSON.stringify(events));
      
      console.log(`📊 Tracked event: ${eventName}`, data);
      
    } catch (error) {
      console.error('❌ Failed to track analytics event:', error);
      // Don't throw - analytics failures shouldn't break functionality
    }
  }
  
  /* ===============================
     OBSERVER PATTERN
  =============================== */
  
  /**
   * Subscribe to state changes
   * @param {Function} callback - Callback function to call on state change
   */
  subscribe(callback) {
    if (typeof callback === 'function') {
      this.observers.push(callback);
    }
  }
  
  /**
   * Unsubscribe from state changes
   * @param {Function} callback - Callback function to remove
   */
  unsubscribe(callback) {
    const index = this.observers.indexOf(callback);
    if (index > -1) {
      this.observers.splice(index, 1);
    }
  }
  
  /**
   * Notify all observers of state change
   */
  notify() {
    this.observers.forEach(callback => {
      try {
        callback(this.state);
      } catch (error) {
        console.error('❌ Observer callback error:', error);
      }
    });
  }
  
  /* ===============================
     UTILITIES
  =============================== */
  
  /**
   * Show a notification to the user
   * @param {string} message - The notification message
   * @param {string} type - The notification type (info, warning, error, success)
   */
  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `comparison-notification comparison-notification-${type}`;
    notification.textContent = message;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
}

// Create global instance
window.comparisonManager = new ComparisonManager();

console.log('✅ ComparisonManager initialized');

// Initialize floating compare button now that ComparisonManager is ready
if (typeof window.initFloatingCompareButton === 'function') {
  window.initFloatingCompareButton();
} else {
  console.warn('⚠️ initFloatingCompareButton not found - will retry on DOMContentLoaded');
  // Retry on DOMContentLoaded in case app.js hasn't loaded yet
  window.addEventListener('DOMContentLoaded', () => {
    if (typeof window.initFloatingCompareButton === 'function') {
      window.initFloatingCompareButton();
    }
  });
}
