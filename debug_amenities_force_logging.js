// Force Debug Logging for Amenities - Inject this into console
console.log('🚀 FORCE DEBUG: Starting amenities debugging...');

// Override console.log to make it more visible
const originalLog = console.log;
console.log = function(...args) {
  originalLog.apply(console, ['🔍 DEBUG:', ...args]);
};

// Check current state
console.log('Current state check:');
console.log('- window.API_BASE_URL:', window.API_BASE_URL);
console.log('- window.insightsData type:', typeof window.insightsData);
console.log('- window.insightsData length:', window.insightsData?.length);
console.log('- currentLocationId:', window.currentLocationId);

// Add click listener with forced logging
document.addEventListener('click', function(e) {
  const amenityBtn = e.target.closest('.amenity-btn');
  if (amenityBtn) {
    console.log('🎯 AMENITY BUTTON CLICKED!');
    console.log('- Button:', amenityBtn);
    console.log('- Amenity type:', amenityBtn.dataset.amenity);
    console.log('- window.insightsData exists:', !!window.insightsData);
    console.log('- window.insightsData is array:', Array.isArray(window.insightsData));
    console.log('- currentLocationId:', window.currentLocationId);
    
    if (!window.insightsData || !Array.isArray(window.insightsData)) {
      console.log('❌ FAILURE: insightsData not loaded');
      alert('DEBUG: insightsData not loaded!');
      return;
    }
    
    if (!window.currentLocationId) {
      console.log('❌ FAILURE: currentLocationId not set');
      alert('DEBUG: No location selected! Click a location pin first.');
      return;
    }
    
    const locationData = window.insightsData.find(d => d.location_id === window.currentLocationId);
    if (!locationData) {
      console.log('❌ FAILURE: Location data not found');
      console.log('- Looking for location_id:', window.currentLocationId);
      console.log('- Available location_ids:', window.insightsData.map(d => d.location_id));
      alert('DEBUG: Location data not found in insightsData!');
      return;
    }
    
    console.log('✅ All checks passed, calling displayAmenitiesOnMap...');
    console.log('- Location data:', locationData);
    
    // Force call the function
    if (typeof displayAmenitiesOnMap === 'function') {
      displayAmenitiesOnMap(window.currentLocationId, amenityBtn.dataset.amenity);
    } else {
      console.log('❌ displayAmenitiesOnMap function not found!');
      alert('DEBUG: displayAmenitiesOnMap function not found!');
    }
  }
}, true); // Use capture phase

// Also check if location click sets currentLocationId
document.addEventListener('click', function(e) {
  // Check if clicked on map location
  setTimeout(() => {
    if (window.currentLocationId) {
      console.log('✅ Location clicked, currentLocationId set to:', window.currentLocationId);
    }
  }, 100);
}, true);

console.log('🚀 FORCE DEBUG: Setup complete. Now click a location, then an amenity button.');