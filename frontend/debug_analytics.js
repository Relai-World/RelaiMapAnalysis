// Debug script to check analytics functionality
console.log('🔧 Debug Analytics Script Loaded');

// Check if volume trends data is loaded
setTimeout(() => {
  console.log('=== ANALYTICS DEBUG REPORT ===');
  
  // 1. Check if VOLUME_TRENDS_DATA exists
  if (typeof VOLUME_TRENDS_DATA !== 'undefined') {
    console.log('✅ VOLUME_TRENDS_DATA loaded');
    console.log('📊 Sample locations:', Object.keys(VOLUME_TRENDS_DATA).slice(0, 5));
  } else {
    console.log('❌ VOLUME_TRENDS_DATA not loaded');
  }
  
  // 2. Check if getVolumeTrends function exists
  if (typeof getVolumeTrends !== 'undefined') {
    console.log('✅ getVolumeTrends function available');
    
    // Test with Gachibowli
    const testData = getVolumeTrends('Gachibowli');
    if (testData) {
      console.log('✅ Test data for Gachibowli:', testData);
    } else {
      console.log('❌ No test data for Gachibowli');
    }
  } else {
    console.log('❌ getVolumeTrends function not available');
  }
  
  // 3. Check if analytics elements exist in DOM
  const analyticsSection = document.querySelector('.analytics-section');
  const analyticsTabs = document.querySelectorAll('.analytics-tab');
  const analyticsPanels = document.querySelectorAll('.analytics-panel');
  
  console.log('🔍 DOM Elements:');
  console.log('  Analytics section:', !!analyticsSection);
  console.log('  Analytics tabs:', analyticsTabs.length);
  console.log('  Analytics panels:', analyticsPanels.length);
  
  if (analyticsSection) {
    console.log('  Section visible:', analyticsSection.offsetHeight > 0);
    console.log('  Section styles:', window.getComputedStyle(analyticsSection).display);
  }
  
  // 4. Check Chart.js
  if (typeof Chart !== 'undefined') {
    console.log('✅ Chart.js loaded');
  } else {
    console.log('❌ Chart.js not loaded');
  }
  
  console.log('=== END DEBUG REPORT ===');
}, 2000);

// Function to manually test analytics
window.testAnalytics = function() {
  console.log('🧪 Manual Analytics Test');
  
  // Try to find and click a location
  const locationElements = document.querySelectorAll('[data-location]');
  console.log('Found location elements:', locationElements.length);
  
  if (locationElements.length > 0) {
    console.log('Clicking first location element...');
    locationElements[0].click();
  }
};

// Function to manually create analytics section
window.createTestAnalytics = function() {
  console.log('🔧 Creating test analytics section');
  
  const testHTML = `
    <div id="test-analytics" style="background: rgba(0,255,0,0.2); border: 2px solid lime; padding: 20px; margin: 20px;">
      <h3 style="color: lime;">TEST ANALYTICS SECTION</h3>
      <div style="display: flex; gap: 10px; margin: 10px 0;">
        <button onclick="alert('Price tab clicked')" style="padding: 10px; background: gold;">Price Analysis</button>
        <button onclick="alert('Volume tab clicked')" style="padding: 10px; background: lightgreen;">Volume Analysis</button>
      </div>
      <div style="background: rgba(255,255,255,0.1); height: 200px; display: flex; align-items: center; justify-content: center;">
        <span style="color: white;">Chart would go here</span>
      </div>
    </div>
  `;
  
  const card = document.getElementById('intel-card');
  if (card) {
    card.insertAdjacentHTML('beforeend', testHTML);
    console.log('✅ Test analytics section added');
  } else {
    console.log('❌ Intel card not found');
  }
};

console.log('🎯 Debug functions available:');
console.log('  - testAnalytics() - Test location clicking');
console.log('  - createTestAnalytics() - Add test analytics section');