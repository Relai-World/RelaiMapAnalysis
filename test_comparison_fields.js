/**
 * Test script to verify comparison feature field structure
 * 
 * Run this in the browser console after loading the comparison modal
 * to verify all fields are displaying correctly.
 */

async function testComparisonFields() {
  console.log('🧪 Testing Comparison Feature Fields...\n');
  
  // Check if comparison manager exists
  if (!window.comparisonManager) {
    console.error('❌ ComparisonManager not found');
    return;
  }
  
  if (!window.comparisonUI) {
    console.error('❌ ComparisonUI not found');
    return;
  }
  
  // Get current comparison data
  const propertyCount = window.comparisonManager.getPropertyCount();
  console.log(`📊 Properties in comparison: ${propertyCount}`);
  
  if (propertyCount < 2) {
    console.warn('⚠️ Need at least 2 properties to test comparison');
    console.log('💡 Add properties using: window.comparisonManager.addProperty(propertyId)');
    return;
  }
  
  // Fetch comparison data
  console.log('🔄 Fetching comparison data...');
  const data = await window.comparisonManager.fetchAllComparisonData();
  
  console.log(`✅ Fetched ${data.properties.length} properties`);
  console.log(`✅ Fetched ${data.locationInsights.size} location insights\n`);
  
  // Test field access for each property
  const requiredFields = [
    'rera_number',
    'projectname',
    'buildername',
    'baseprojectprice',
    'project_type',
    'communitytype',
    'total_land_area',
    'project_launch_date',
    'possession_date',
    'construction_status',
    'price_per_sft',
    'powerbackup',
    'visitor_parking',
    'sqfeet',
    'areaname',
    'google_place_rating',
    'external_amenities'
  ];
  
  console.log('🔍 Testing field access for each property:\n');
  
  data.properties.forEach((prop, index) => {
    console.log(`Property ${index + 1}: ${prop.projectname || 'Unnamed'}`);
    console.log('─'.repeat(50));
    
    const results = {
      found: [],
      missing: [],
      topLevel: [],
      fullDetails: []
    };
    
    requiredFields.forEach(field => {
      const topLevel = prop[field];
      const fullDetails = prop.full_details?.[field];
      const value = topLevel || fullDetails;
      
      if (value !== null && value !== undefined && value !== '' && value !== 0) {
        results.found.push(field);
        if (topLevel) results.topLevel.push(field);
        if (fullDetails) results.fullDetails.push(field);
      } else {
        results.missing.push(field);
      }
    });
    
    console.log(`✅ Found: ${results.found.length}/${requiredFields.length} fields`);
    console.log(`📍 Top-level: ${results.topLevel.length} fields`);
    console.log(`📦 Full details: ${results.fullDetails.length} fields`);
    
    if (results.missing.length > 0) {
      console.log(`⚠️ Missing/Empty: ${results.missing.join(', ')}`);
    }
    
    // Test grid score calculation
    if (prop.areaname) {
      const insights = data.locationInsights.get(prop.areaname.toLowerCase());
      if (insights) {
        const gridScore = (
          (insights.connectivity_score || 0) + 
          (insights.amenities_score || 0) + 
          ((insights.growth_score || 0) * 10) + 
          ((insights.investment_score || 0) * 10)
        ) / 4;
        console.log(`📊 Grid Score: ${gridScore.toFixed(1)}`);
      } else {
        console.log('⚠️ No location insights found');
      }
    }
    
    console.log('');
  });
  
  // Test amenities
  console.log('🏊 Testing Amenities:\n');
  data.properties.forEach((prop, index) => {
    const amenities = prop.external_amenities || prop.full_details?.external_amenities;
    const location = prop.google_place_location || prop.full_details?.google_place_location;
    
    console.log(`Property ${index + 1}: ${prop.projectname || 'Unnamed'}`);
    
    if (amenities && amenities.trim()) {
      const amenitiesList = amenities.split(',').map(a => a.trim()).filter(Boolean);
      console.log(`  ✅ Has ${amenitiesList.length} amenities in table`);
      console.log(`  📝 Sample: ${amenitiesList.slice(0, 3).join(', ')}`);
    } else if (location) {
      console.log(`  ⚠️ No amenities in table, but has location data`);
      console.log(`  💡 Will fetch from Google Places API`);
      
      // Try to parse location
      try {
        let lat, lng;
        if (typeof location === 'string') {
          if (location.startsWith('{')) {
            const parsed = JSON.parse(location.replace(/'/g, '"'));
            lat = parsed.lat;
            lng = parsed.lng;
          } else if (location.includes(',')) {
            const parts = location.split(',');
            lat = parseFloat(parts[0]);
            lng = parseFloat(parts[1]);
          }
        } else if (typeof location === 'object') {
          lat = location.lat;
          lng = location.lng;
        }
        
        if (lat && lng) {
          console.log(`  📍 Coordinates: ${lat}, ${lng}`);
        } else {
          console.log(`  ❌ Could not parse coordinates`);
        }
      } catch (e) {
        console.log(`  ❌ Error parsing location: ${e.message}`);
      }
    } else {
      console.log(`  ❌ No amenities or location data`);
    }
    console.log('');
  });
  
  console.log('✅ Test complete!\n');
  console.log('💡 To open comparison modal: window.comparisonUI.open()');
}

// Auto-run if in browser console
if (typeof window !== 'undefined') {
  console.log('📋 Comparison Field Test Script Loaded');
  console.log('💡 Run: testComparisonFields()');
}
