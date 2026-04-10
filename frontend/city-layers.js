/**
 * City-based Layer Management System
 * Dynamically shows/hides layers based on the current city
 */

// City boundaries (approximate)
const CITY_BOUNDS = {
  hyderabad: {
    center: [78.38, 17.44],
    bounds: [[77.8, 17.0], [79.0, 17.9]],
    name: 'Hyderabad'
  },
  bangalore: {
    center: [77.59, 12.97],
    bounds: [[77.3, 12.7], [77.9, 13.2]],
    name: 'Bangalore'
  }
};

// Layer configuration for each city
const CITY_LAYERS = {
  hyderabad: {
    layers: [
      { id: 'highways-layer', name: 'Highways', icon: 'highway.png', tooltip: 'Major Highways & Arterial Roads' },
      { id: 'metro-layer', name: 'Metro', icon: 'train.png', tooltip: 'Hyderabad Metro Corridors' },
      { id: 'orr-layer', name: 'ORR', icon: 'orr.png', tooltip: 'Outer Ring Road (ORR)' },
      { id: 'lakes-layer', name: 'Lakes', icon: 'lakes.png', tooltip: 'Lakes & Water Bodies' },
      { id: 'rrr-layer', name: 'RRR', icon: 'rrr.png', tooltip: 'Regional Ring Road (RRR)' },
      { id: 'hmda-layer', name: 'HMDA', icon: 'HMDA.png', tooltip: 'HMDA Masterplan Boundary' },
      { id: 'hmda-masterplan-layer', name: 'Plan 2031', icon: 'layers.png', tooltip: 'HMDA Master Plan 2031 - Land Use Zones' },
      { id: 'flood-risk-layer', name: 'Floods', icon: 'floods.png', tooltip: 'Drainage Networks & Flood Risk Heatmap' }
    ]
  },
  bangalore: {
    layers: [
      { id: 'blr-highways-layer', name: 'Highways', icon: 'highway.png', tooltip: 'Major Highways & Arterial Roads' },
      { id: 'blr-metro-layer', name: 'Metro', icon: 'train.png', tooltip: 'Bangalore Metro (Namma Metro)' },
      { id: 'blr-orr-layer', name: 'ORR', icon: 'orr.png', tooltip: 'Outer Ring Road (ORR)' },
      { id: 'blr-lakes-layer', name: 'Lakes', icon: 'lakes.png', tooltip: 'Lakes & Water Bodies' },
      { id: 'blr-prr-layer', name: 'PRR', icon: 'rrr.png', tooltip: 'Peripheral Ring Road (PRR)' },
      { id: 'blr-bbmp-layer', name: 'BBMP', icon: 'HMDA.png', tooltip: 'BBMP Boundary' },
      { id: 'blr-floods-layer', name: 'Floods', icon: 'floods.png', tooltip: 'Flood Prone Areas' }
    ]
  }
};

/**
 * Detect current city based on map center
 */
function detectCity(map) {
  const center = map.getCenter();
  const lng = center.lng;
  const lat = center.lat;

  // Check if within Hyderabad bounds
  if (lng >= CITY_BOUNDS.hyderabad.bounds[0][0] && lng <= CITY_BOUNDS.hyderabad.bounds[1][0] &&
      lat >= CITY_BOUNDS.hyderabad.bounds[0][1] && lat <= CITY_BOUNDS.hyderabad.bounds[1][1]) {
    return 'hyderabad';
  }

  // Check if within Bangalore bounds
  if (lng >= CITY_BOUNDS.bangalore.bounds[0][0] && lng <= CITY_BOUNDS.bangalore.bounds[1][0] &&
      lat >= CITY_BOUNDS.bangalore.bounds[0][1] && lat <= CITY_BOUNDS.bangalore.bounds[1][1]) {
    return 'bangalore';
  }

  // Default to Hyderabad if can't detect
  return 'hyderabad';
}

/**
 * Update layer controls based on current city
 */
function updateLayerControls(city) {
  const layerControls = document.getElementById('layer-controls');
  if (!layerControls) return;

  const cityConfig = CITY_LAYERS[city];
  if (!cityConfig) return;

  // Clear existing controls
  layerControls.innerHTML = '';

  // Add city-specific layer controls
  cityConfig.layers.forEach(layer => {
    const label = document.createElement('label');
    label.className = 'layer-toggle';
    label.setAttribute('data-tippy-content', layer.tooltip);

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = layer.id.replace('-layer', '');
    checkbox.setAttribute('data-layer', layer.id);

    const card = document.createElement('div');
    card.className = 'layer-card';

    const img = document.createElement('img');
    img.src = `assets/${layer.icon}`;
    img.alt = layer.name;

    const span = document.createElement('span');
    span.textContent = layer.name;

    card.appendChild(img);
    card.appendChild(span);
    label.appendChild(checkbox);
    label.appendChild(card);
    layerControls.appendChild(label);
  });

  console.log(`✅ Layer controls updated for ${CITY_BOUNDS[city].name}`);
}

/**
 * Initialize city-based layer system
 */
function initCityLayers(map) {
  // Detect initial city
  const currentCity = detectCity(map);
  window.currentCity = currentCity;
  window.manualCitySelection = false; // Track if user manually selected a city
  
  console.log(`🌆 Detected city: ${CITY_BOUNDS[currentCity].name}`);
  
  // Update layer controls
  updateLayerControls(currentCity);

  // Re-attach layer toggle event listeners after updating controls
  if (window.attachLayerToggles) {
    window.attachLayerToggles();
  }

  // Listen for map movement to detect city changes (only if not manually selected)
  map.on('moveend', () => {
    // Skip auto-detection if user manually selected a city
    if (window.manualCitySelection) return;
    
    const newCity = detectCity(map);
    if (newCity !== window.currentCity) {
      console.log(`🌆 City changed: ${CITY_BOUNDS[window.currentCity].name} → ${CITY_BOUNDS[newCity].name}`);
      window.currentCity = newCity;
      updateLayerControls(newCity);
      
      // Re-attach event listeners
      if (window.attachLayerToggles) {
        window.attachLayerToggles();
      }
    }
  });
}

// Export for use in app.js
window.initCityLayers = initCityLayers;
window.detectCity = detectCity;
window.updateLayerControls = updateLayerControls;
window.CITY_BOUNDS = CITY_BOUNDS;
window.CITY_LAYERS = CITY_LAYERS;
