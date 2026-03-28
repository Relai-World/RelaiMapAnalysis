console.log("App.js Loaded - V 2.1 - Future Development Fixed - API URLs Corrected");

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const map = new maplibregl.Map({
  container: "map",
  // Neutral, slightly desaturated light basemap to match luxury UI
  style: 'https://tiles.openfreemap.org/styles/liberty',

  center: [78.38, 17.44],
  zoom: 11,
  minZoom: 4,
  maxZoom: 18
});

// Load amenity icons when map is ready
map.on('load', () => {
  // Map of amenity types to icon files
  const amenityIcons = {
    'hospitals': 'images/hospital.png',
    'schools': 'images/schools.png',
    'parks': 'images/tree.png',
    'malls': 'images/mall.png',
    'restaurants': 'images/dinner.png',
    'banks': 'images/bank.png',
    'metro': 'images/metro.png'
  };

  // Load each icon
  Object.entries(amenityIcons).forEach(([type, path]) => {
    map.loadImage(path, (error, image) => {
      if (error) {
        console.error(`Failed to load ${type} icon:`, error);
        return;
      }
      if (!map.hasImage(`icon-${type}`)) {
        map.addImage(`icon-${type}`, image);
      }
    });
  });
});

// 🚀 SUPABASE DIRECT CONNECTION - No more API server needed!
const SUPABASE_URL = "https://ihraowxbduhlichzszgk.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlocmFvd3hiZHVobGljaHpzemdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk5MDU5OTEsImV4cCI6MjA2NTQ4MTk5MX0.9SGeXWpk4_OI2qMPyfCfVtUqar6q62-ZFifaA3lc3BE";

// Google Places API Key is handled by the backend API
// No API key needed in frontend - all requests go through Python API

// Supabase RPC call helper
async function callSupabaseRPC(functionName, params = {}) {
  console.log(`🔍 Calling Supabase RPC: ${functionName}`, params);

  try {
    const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/${functionName}`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_KEY,
        'Authorization': `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });

    console.log(`🔍 Response status: ${response.status}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ Supabase RPC error: ${response.statusText}`, errorText);
      throw new Error(`Supabase RPC error: ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log(`✅ RPC ${functionName} success:`, data);
    return data;
  } catch (error) {
    console.error(`❌ RPC ${functionName} failed:`, error);
    throw error;
  }
}

// 🚀 EARLY FETCH: Start getting data immediately while map initializes
const insightsPromise = callSupabaseRPC('get_all_insights');

// Store insights data globally for amenities
window.insightsData = null;

// Navigation control removed - cleaner interface

let activeMarker = null;
let clickMarker = null; // lightweight marker for generic map clicks

/* ===============================
   TEXT HELPERS (SCALE-ALIGNED - V2)
=============================== */
function sentimentText(v) {
  if (v >= 0.05) return "Positive";
  if (v <= -0.05) return "Negative";
  return "Neutral";
}

function growthText(v) {
  if (v >= 0.8) return "High";
  if (v >= 0.5) return "Medium";
  return "Low";
}

function investmentText(v) {
  if (v >= 0.7) return "Excellent";
  if (v >= 0.5) return "Good";
  return "Average";
}

/* ===============================
   UI – LAYERS ONLY
=============================== */
// Layer toggles are now handled inline by MapLibre layer interactions below.

/* ===============================
   GLOBAL DATA & HELPERS
=============================== */
let currentCostData = null;
let currentAmenityList = []; // Store list of amenities for PDF
let currentAmenityType = ""; // Store current type (e.g., "Hospitals")
let currentAmenityLayer = null; // Global tracker for active amenity layer
let currentLocationId = null; // Global tracker for active location
let currentPopup = null; // Global tracker for active popup
let futureDevPopup = null; // Global tracker for future development popup

/* ===============================
   DYNAMIC FACTS GENERATOR (No More Hardcoded Strings)
=============================== */

// 1. FACT GENERATORS (Consuming Backend Summaries)
function getSentimentFact(p) {
  return p.sentiment_summary || "Analyzing sentiment...";
}

function getGrowthFact(p) {
  return p.growth_summary || "Evaluating infrastructure...";
}

function getInvestFact(p) {
  return p.invest_summary || "Calculating returns...";
}

// 2. MARKDOWN FORMATTER - Convert markdown to HTML for better display
function formatMarkdownText(text) {
  if (!text) return text;

  return text
    // Convert **bold** to <strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Convert *italic* to <em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Convert bullet points - • to proper bullets with spacing
    .replace(/^- /gm, '• ')
    .replace(/\n- /g, '<br>• ')
    // Add line breaks for better readability after periods followed by bullets
    .replace(/\. - /g, '.<br><br>• ')
    // Add line breaks after sentences for better flow
    .replace(/\. ([A-Z])/g, '.<br>$1')
    // Clean up multiple spaces
    .replace(/\s+/g, ' ')
    // Clean up multiple line breaks
    .replace(/<br>\s*<br>\s*<br>/g, '<br><br>')
    .trim();
}

// 3. METRIC EXPAND FUNCTION
// 3. METRIC EXPAND FUNCTION
function expandMetric(clickedBox) {
  const allBoxes = document.querySelectorAll('.metric-card');
  const isCurrentlyExpanded = clickedBox.classList.contains('expanded');

  const intelCard = document.getElementById('intel-card');

  // If clicking the same expanded box, collapse all
  if (isCurrentlyExpanded) {
    allBoxes.forEach(box => {
      box.classList.remove('expanded', 'collapsed');
    });
    return;
  }

  // Expand clicked box and collapse others
  allBoxes.forEach(box => {
    if (box === clickedBox) {
      box.classList.add('expanded');
      box.classList.remove('collapsed');
    } else {
      box.classList.add('collapsed');
      box.classList.remove('expanded');
    }
  });

  // Scroll to show the expanded card smoothly
  if (intelCard) {
    setTimeout(() => {
      const cardTop = clickedBox.offsetTop;
      const cardHeight = clickedBox.offsetHeight;
      const containerHeight = intelCard.clientHeight;
      const currentScroll = intelCard.scrollTop;

      const cardBottom = cardTop + cardHeight;
      const visibleTop = currentScroll;
      const visibleBottom = currentScroll + containerHeight;

      if (cardTop < visibleTop || cardBottom > visibleBottom) {
        intelCard.scrollTo({
          top: cardTop - 20,
          behavior: 'smooth'
        });
      }
    }, 100);
  }
}

window.expandMetric = expandMetric;

// Helper function to generate comparison bar HTML
function generateComparisonBar(localityScore, cityAvg, percentile) {
  if (!cityAvg || percentile === null || percentile === undefined) return '';
  
  const localityPos = Math.min(Math.max(localityScore, 0), 100);
  const cityAvgPos = Math.min(Math.max(cityAvg, 0), 100);
  
  // Better percentile wording: if percentile is 94, they beat 94% of locations
  const percentileText = percentile >= 90 ? `Top 10%` : 
                         percentile >= 75 ? `Top 25%` :
                         percentile >= 50 ? `Top 50%` :
                         percentile >= 25 ? `Top 75%` : `Bottom 25%`;
  
  return `
    <div class="comparison-section">
      <div class="comparison-bars-container">
        <!-- Single Bar with Both Labels -->
        <div class="comparison-row">
          <div class="comparison-labels-top">
            <span class="comparison-label">This locality</span>
            <span class="comparison-label-right">City avg: ${cityAvg}</span>
          </div>
          <div class="comparison-bar-track">
            <div class="comparison-bar-fill locality-bar" style="width: ${localityPos}%"></div>
            <div class="comparison-marker" style="left: ${cityAvgPos}%">
              <div class="marker-line"></div>
              <div class="avg-marker-label">avg</div>
            </div>
          </div>
          <div style="height: 16px;"></div>
        </div>
      </div>
      
      <div class="percentile-badge">${percentileText} of Hyderabad</div>
    </div>
  `;
}

// 2. THE INTELLIGENCE ENGINE (Fetches Deep Data)
// 2. THE INTELLIGENCE ENGINE (Moved to Backend: aggregation/generate_smart_facts.py)
// Logic simplified to consume API response directly.

/* ===============================
   PDF REPORT GENERATOR
=============================== */
function generateReport(p) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  let y = 20;

  // TITLE
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.setTextColor(37, 99, 235); // Blue
  doc.text("HYDERABAD INTELLIGENCE", 14, y);
  y += 10;

  doc.setFontSize(14);
  doc.setTextColor(60);
  doc.text(`Location Analysis: ${p.location}`, 14, y);
  y += 10;

  doc.setFontSize(10);
  doc.setTextColor(150);
  doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, y);
  y += 10;

  doc.setDrawColor(200);
  doc.line(14, y, 196, y);
  y += 15;

  // 1. KEY METRICS
  doc.setFontSize(14);
  doc.setTextColor(0);
  doc.setFont("helvetica", "bold");
  doc.text("Key Metrics & Scores", 14, y);
  y += 10;

  doc.setFontSize(11);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(40);

  const metrics = [
    { label: "Market Sentiment", val: sentimentText(p.avg_sentiment), score: p.avg_sentiment.toFixed(2) },
    { label: "Growth Potential", val: growthText(p.growth_score), score: p.growth_score.toFixed(1) },
    { label: "Investment Rating", val: investmentText(p.investment_score), score: p.investment_score.toFixed(1) }
  ];

  metrics.forEach(m => {
    doc.text(`• ${m.label}: ${m.val} (Score: ${m.score})`, 20, y);
    y += 7;
  });
  y += 8;

  // 2. DETAILED INSIGHTS
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.setTextColor(0);
  doc.text("Strategic Insights", 14, y);
  y += 10;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor(50);

  const insights = [
    { title: "Sentiment", text: getSentimentFact(p).replace(/<[^>]*>?/gm, '') },
    { title: "Growth Drivers", text: getGrowthFact(p).replace(/<[^>]*>?/gm, '') },
    { title: "Investment View", text: getInvestFact(p).replace(/<[^>]*>?/gm, '') }
  ];

  insights.forEach(i => {
    doc.setFont("helvetica", "bold");
    doc.text(i.title + ":", 20, y);
    doc.setFont("helvetica", "normal");

    // Simple word wrap logic for long text
    const splitText = doc.splitTextToSize(i.text, 140);
    doc.text(splitText, 55, y);
    y += (splitText.length * 5) + 6;
  });

  y += 5;

  // 3. PROPERTY COSTS (If Available)
  if (currentCostData) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(0);
    doc.text("Property Market Data (2025)", 14, y);
    y += 10;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    doc.setTextColor(50);

    doc.text(`• Average Price/SqFt:  Rs ${currentCostData.avgSqft.toLocaleString()}`, 20, y);
    y += 7;
    doc.text(`• Price Range (SqFt):  Rs ${currentCostData.minSqft.toLocaleString()} - ${currentCostData.maxSqft.toLocaleString()}`, 20, y);
    y += 7;
    doc.text(`• Average Base Price:  Rs ${currentCostData.avgBase} Cr`, 20, y);
    y += 7;
    doc.text(`• Base Price Range:    Rs ${currentCostData.minBase} - ${currentCostData.maxBase} Cr`, 20, y);
    y += 7;
    doc.text(`• Properties Analyzed: ${currentCostData.count}`, 20, y);
    y += 12;
  }

  // 4. NEARBY AMENITIES (If Available)
  if (currentAmenityList && currentAmenityList.length > 0) {
    if (y > 250) { doc.addPage(); y = 20; }
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(0);
    doc.text(`Nearby ${currentAmenityType} (${currentAmenityList.length})`, 14, y);
    y += 10;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(50);

    currentAmenityList.slice(0, 10).forEach(a => {
      doc.text(`• ${a.name} (${a.distance_km} km)`, 20, y);
      y += 6;
      if (y > 275) { doc.addPage(); y = 20; }
    });

    if (currentAmenityList.length > 10) {
      doc.setFont("helvetica", "italic");
      doc.text(`... and ${currentAmenityList.length - 10} more.`, 20, y);
      y += 8;
    }
  }

  // FOOTER
  doc.setFontSize(9);
  doc.setTextColor(180);
  doc.text("Source: Hyderabad Real Estate Intelligence Platform", 14, 285);
  doc.text("Disclaimer: Data is for informational purposes only.", 14, 290);

  doc.save(`${p.location}_Detailed_Report.pdf`);
}

/* ===============================
   MAP LOAD
=============================== */
map.on("load", async () => {

  /* =====================================================
     📍 BASE TILE URL LOGIC & PRE-FETCHING
  ===================================================== */
  const BASE_TILES_URL = "maptiles";

  // SNAPPY LOADING: Pre-fetch headers for all PMTiles files
  const pmtilesLayers = ["highways", "metro", "orr", "lakes"];
  pmtilesLayers.forEach(name => {
    const p = new pmtiles.PMTiles(`${BASE_TILES_URL}/${name}.pmtiles`);
    p.getHeader().then(() => console.log(`✓ Warm-up: ${name} data ready`))
      .catch(e => console.warn(`Warm-up failed for ${name}`, e));
  });

  /* =====================================================
     🏗️ ADD SOURCES & LAYERS (GHOST LOADING MODE)
  ===================================================== */



  map.addSource("orr-source", {
    type: "vector", url: `pmtiles://${BASE_TILES_URL}/orr.pmtiles`,
    minzoom: 0,
    maxzoom: 24  // Extended to match layer maxzoom
  });
  map.addLayer({
    id: "orr-layer",
    type: "line",
    source: "orr-source",
    "source-layer": "orr", // Will update based on console output
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#000000ff", "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.5, 18, 6], "line-blur": 1, "line-opacity": 0 }, // Ghost state - visible at all zooms when activated
    minzoom: 0,
    maxzoom: 24
  });

  // 3. Highways
  map.addSource("highways-source", {
    type: "vector", url: `pmtiles://${BASE_TILES_URL}/highways.pmtiles`,
    minzoom: 0,
    maxzoom: 24  // Extended to match layer maxzoom
  });
  map.addLayer({
    id: "highways-layer",
    type: "line",
    source: "highways-source",
    "source-layer": "highways",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#64008fff", "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.2, 18, 4.8], "line-blur": 1, "line-opacity": 0 }, // Ghost state - visible at all zooms when activated
    minzoom: 0,
    maxzoom: 24
  });

  // 4. Metro (Using GeoJSON directly to ensure LineStrings are rendered)
  map.addSource("metro-source", {
    type: "geojson",
    data: "data/metro.geojson"
  });

  // Metro Tracks (Lines)
  map.addLayer({
    id: "metro-layer",
    type: "line",
    source: "metro-source",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#ef0000",
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.5, 18, 5],
      "line-opacity": 0 // Ghost state - visible at all zooms when activated
    },
    minzoom: 0,
    maxzoom: 24
  });

  // Metro Stations (Points)
  map.addLayer({
    id: "metro-stations-layer",
    type: "circle",
    source: "metro-source",
    filter: ["==", ["geometry-type"], "Point"],
    layout: { visibility: "visible" },
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 3, 15, 8],
      "circle-color": "#ffffff",
      "circle-stroke-color": "#f00b0b",
      "circle-stroke-width": 2,
      "circle-opacity": 0,
      "circle-stroke-opacity": 0
    },
    minzoom: 0,
    maxzoom: 24
  });

  // 5. RRR (Regional Ring Road)
  map.addSource("rrr-source", {
    type: "geojson",
    data: "maptiles/rrr.geojson"
  });

  map.addLayer({
    id: "rrr-layer",
    type: "line",
    source: "rrr-source",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#ff8c00", // Dark Orange
      "line-width": 3,
      "line-opacity": 0 // Ghost state - visible at all zooms when activated
    },
    minzoom: 0,
    maxzoom: 24
  });

  // 6. HMDA Boundary
  map.addSource("hmda-source", {
    type: "geojson",
    data: "maptiles/hmda.geojson"
  });

  map.addLayer({
    id: "hmda-layer",
    type: "line",
    source: "hmda-source",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#4169E1", // Royal Blue
      "line-width": 2,
      "line-dasharray": [4, 2], // Dashed line for boundary
      "line-opacity": 0 // Ghost state - visible at all zooms when activated
    },
    minzoom: 0,
    maxzoom: 24
  });

  // 6.5. HMDA Master Plan 2031 Image Overlay
  map.addSource('hmda-masterplan-2031', {
    type: 'image',
    url: 'data/hmda_masterplan.png',
    coordinates: [
      [78.00, 17.90],     // top-left [lng, lat]
      [79.05, 17.90],     // top-right
      [79.05, 16.97],     // bottom-right
      [78.00, 16.97]      // bottom-left
    ]
  });

  map.addLayer({
    id: 'hmda-masterplan-layer',
    type: 'raster',
    source: 'hmda-masterplan-2031',
    paint: {
      'raster-opacity': 0,
      'raster-fade-duration': 300,
      'raster-resampling': 'linear'
    }
  });

  // 1. Lakes (Moved to end)
  map.addSource("lakes-source", {
    type: "vector",
    url: `pmtiles://${BASE_TILES_URL}/lakes.pmtiles`,
    minzoom: 0,
    maxzoom: 24
  });
  map.addLayer({
    id: "lakes-layer",
    type: "fill",
    source: "lakes-source",
    "source-layer": "lakes",
    layout: { visibility: "visible" },
    paint: {
      "fill-color": "#0077ff",
      "fill-opacity": 0 // Ghost state - visible at all zooms when activated
    },
    minzoom: 0,
    maxzoom: 24
  });
  console.log("✅ Lakes layer added successfully");

  // 7. Natural Drainage Network (REAL DATA from Felt Pipeline)
  map.addSource("flood-drainage-source", {
    type: "vector",
    tiles: ["https://us1.data-pipeline.felt.com/vectortile/6694b342-6d34-50a2-8359-9bba00004453/{z}/{x}/{y}.pbf?query=eJyrVkrLzClJLSpWssorzcmpBQAzHAYr"],
    minzoom: 0,
    maxzoom: 20
  });

  map.addLayer({
    id: "flood-risk-layer",
    type: "line",
    source: "flood-drainage-source",
    "source-layer": "parsed",
    layout: {
      "visibility": "visible",
      "line-join": "round",
      "line-cap": "round"
    },
    paint: {
      "line-color": [
        "match", ["get", "ORDER"],
        7, "#1e3a8a", // 7th Order (Massive River/Extreme Risk) -> Deep Navy Blue
        6, "#0000ffff", // 6th Order (Major Drain/High Risk) -> Strong Royal Blue
        5, "#004cf1ff", // 5th Order (Medium Drain/Moderate Risk) -> Solid Blue
        4, "#1100ffff", // 4th Order (Small Drain/Low Risk) -> Standard Blue
        "#2b00ffff"     // 3rd Order & Below (Micro Drain/Lowest) -> Light/Pale Frozen Blue
      ],
      "line-width": [
        "interpolate", ["linear"], ["zoom"],
        8, ["match", ["get", "ORDER"], 7, 3.5, 6, 2.5, 5, 1.5, 0.8],
        12, ["match", ["get", "ORDER"], 7, 7.0, 6, 5.0, 5, 3.0, 1.5],
        16, ["match", ["get", "ORDER"], 7, 12.0, 6, 9.0, 5, 6.0, 3.0]
      ],
      "line-opacity": 0 // Ghost state - visible at all zooms when activated
    },
    minzoom: 0,
    maxzoom: 24
  });

  // Keep Stagnation Points as a sub-layer
  map.addSource("flood-stagnation-source", {
    type: "geojson",
    data: "maptiles/flood_stagnation_points.geojson"
  });

  map.addLayer({
    id: "flood-points-layer",
    type: "circle",
    source: "flood-stagnation-source",
    layout: { visibility: "visible" },
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 4, 16, 12],
      "circle-color": "#f0abfc", // Light Magenta/Purple glow
      "circle-stroke-color": "#c026d3", // Deep Magenta
      "circle-stroke-width": 2,
      "circle-opacity": 0,
      "circle-stroke-opacity": 0,
      "circle-blur": 0.5 // Softer look for stagnation points
    },
    minzoom: 0,
    maxzoom: 24
  });


  // 8. Rainfall Data (REAL DATA from TSDPS via Felt)
  map.addSource("rainfall-source", {
    type: "geojson",
    data: "maptiles/rainfall_data.geojson"
  });

  map.addLayer({
    id: "rainfall-layer",
    type: "circle",
    source: "rainfall-source",
    layout: { visibility: "visible" },
    paint: {
      "circle-radius": [
        "step", ["coalesce", ["get", "rainfall_mm"], 0],
        4,          // <2.4
        2.4, 7,     // Light
        15.5, 14,   // Moderate
        64.4, 22,   // Heavy
        115.5, 32,  // Very Heavy
        204.4, 46   // Extreme
      ],
      "circle-color": [
        "step", ["coalesce", ["get", "rainfall_mm"], 0],
        "#A5D8F3", // Default/Very Light (<2.4)
        2.4, "#A5D8F3", // Light (2.4-15.5) -> Light Blue
        15.5, "#A2D246", // Moderate (15.5-64.4) -> Lime/Light Green
        64.4, "#16A34A", // Heavy (64.4-115.5) -> Dark Green
        115.5, "#FF6A00", // Very Heavy (115.5-204.4) -> Orange
        204.4, "#DC2626"  // Extremely Heavy (>204.4) -> Red
      ],
      "circle-stroke-color": "#1E293B", // Dark mapbox stroke for contrast
      "circle-stroke-width": 1,
      "circle-opacity": 0, // Ghost state - visible at all zooms when activated
      "circle-stroke-opacity": 0
    },
    minzoom: 0,
    maxzoom: 24
  });

  // Adding Labels for Rainfall mm
  map.addLayer({
    id: "rainfall-labels",
    type: "symbol",
    source: "rainfall-source",
    layout: {
      "text-field": ["to-string", ["get", "rainfall_mm"]],
      "text-size": [
        "step", ["coalesce", ["get", "rainfall_mm"], 0],
        0,          // <2.4
        2.4, 10,    // Light
        15.5, 12,   // Moderate
        64.4, 14,   // Heavy
        115.5, 15,  // Very Heavy
        204.4, 16   // Extreme
      ],
      "text-allow-overlap": true,
      "text-ignore-placement": true,
      "text-font": ["Noto Sans Bold"],
      "visibility": "visible"
    },
    paint: {
      "text-color": "#111827",
      "text-halo-color": "#ffffff",
      "text-halo-width": 1.2,
      "text-opacity": 0 // Ghost state - visible at all zooms when activated
    }
  });



  // MAP INIT (USING LOCALLY HOSTED PMTILES) - removed to avoid conflict

  try {
    const data = await insightsPromise;

    // Store globally for amenities
    window.insightsData = data;

    console.log("🔍 DEBUG: Raw insights data:", data);
    console.log("🔍 DEBUG: Data type:", typeof data, "Is array:", Array.isArray(data));

    if (Array.isArray(data) && data.length > 0) {
      console.log("🔍 DEBUG: First location:", data[0]);
      console.log("🔍 DEBUG: Coordinates:", data[0].longitude, data[0].latitude);
    }

    const searchInput = document.getElementById("location-search");
    const searchResults = document.getElementById("search-results");

    if (searchInput && searchResults) {
      searchInput.addEventListener("focus", () => {
        // We don't necessarily hide the card on focus if a location is already selected,
        // but we should ensure the UI state is consistent.
      });

      // Input Event (searches news_balanced_corpus_1 via API)
      let searchDebounceTimer = null;
      searchInput.addEventListener("input", (e) => {
        const val = e.target.value;
        searchResults.innerHTML = "";

        const card = document.getElementById("intel-card");
        const emptyState = document.getElementById("empty-state");

        if (val.length < 1) {
          searchResults.style.display = "none";
          if (card.style.display === "none") {
            if (emptyState) emptyState.style.display = "flex";
          }
          clearTimeout(searchDebounceTimer);
          return;
        }

        if (emptyState) emptyState.style.display = "none";

        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(async () => {
          try {
            const matches = await callSupabaseRPC('search_locations_func', { search_query: val });
            searchResults.innerHTML = "";

            if (Array.isArray(matches) && matches.length > 0) {
              matches.forEach(match => {
                const div = document.createElement("div");
                div.className = "search-result-item";
                div.textContent = match.location_name;
                if (match.location_name.toLowerCase() === val.toLowerCase()) {
                  div.style.background = "rgba(59, 130, 246, 0.2)";
                }
                div.onclick = () => {
                  searchInput.value = match.location_name;
                  searchResults.style.display = "none";
                  // Try to match in insights data for full location details
                  const insightMatch = Array.isArray(data)
                    ? data.find(d => d.location.toLowerCase() === match.location_name.toLowerCase())
                    : null;
                  if (insightMatch) {
                    handleLocationSelect(insightMatch);
                    loadPropertiesForLocation(insightMatch.location);
                  } else {
                    loadPropertiesForLocation(match.location_name);
                  }
                };
                searchResults.appendChild(div);
              });
              searchResults.style.display = "block";
            } else {
              const div = document.createElement("div");
              div.className = "search-result-item";
              div.style.cursor = "default";
              div.style.fontStyle = "italic";
              div.style.color = "#94a3b8";
              div.textContent = "No result found";
              searchResults.appendChild(div);
              searchResults.style.display = "block";
            }
          } catch (err) {
            console.error("Search error:", err);
          }
        }, 250);
      });

      // Enter Key Navigation
      searchInput.addEventListener("keydown", async (e) => {
        if (e.key === "Enter") {
          const val = searchInput.value;
          if (!val.trim()) return;

          try {
            const matches = await callSupabaseRPC('search_locations_func', { search_query: val });
            const bestMatch = Array.isArray(matches) && matches.length > 0 ? matches[0] : null;

            if (bestMatch) {
              searchInput.value = bestMatch.location_name;
              searchResults.style.display = "none";
              searchInput.blur();
              const insightMatch = Array.isArray(data)
                ? data.find(d => d.location.toLowerCase() === bestMatch.location_name.toLowerCase())
                : null;
              if (insightMatch) {
                handleLocationSelect(insightMatch);
                loadPropertiesForLocation(insightMatch.location);
              } else {
                loadPropertiesForLocation(bestMatch.location_name);
              }
            } else {
              if (searchResults.style.display === "none") {
                searchInput.dispatchEvent(new Event('input'));
              }
            }
          } catch (err) {
            console.error("Search error:", err);
          }
        }
      });

      // Hide on click outside
      document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
          searchResults.style.display = "none";
        }
      });
    }

    if (!Array.isArray(data)) {
      console.error("Invalid data format received from API:", data);
      return;
    }

    map.addSource("locations", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: data.map(d => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: [d.longitude, d.latitude] },
          properties: d
        }))
      }
    });

    // GLOW RING (renders behind the dot for depth) – Minimal Bronze Glow
    map.addLayer({
      id: "location-glow",
      type: "circle",
      source: "locations",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 8, 15, 12],
        "circle-color": "#A68A3D", // Bronze
        "circle-opacity": 0.1,
        "circle-stroke-width": 0,
        "circle-blur": 2
      }
    });

    // CHARCOAL CORE — Sharp & Minimal
    map.addLayer({
      id: "location-core",
      type: "circle",
      source: "locations",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 3.5, 14, 5.5],
        "circle-color": "#1A1C1E", // Deep Onyx
        "circle-stroke-color": "#FFFFFF",
        "circle-stroke-width": 1.5,
        "circle-stroke-opacity": 1
      }
    });

    // Apply any pending filter sent from parent dashboard before layers were ready
    if (window._relaiFilterAreas && typeof window.applyAreaFilter === 'function') {
      window.applyAreaFilter(window._relaiFilterAreas);
      window._relaiFilterAreas = null;
    }
  } catch (err) {
    console.error("Failed to load locations:", err);
  }

  /* =====================================================
     LAYER TOGGLE (GHOST FADE LOGIC)
  ===================================================== */
  const opacities = {
    "lakes-layer": 0.8,
    "orr-layer": 0.9,
    "highways-layer": 0.8,
    "metro-layer": 1.0,
    "rrr-layer": 0.8,
    "schools-layer": 0.9,
    "hmda-layer": 0.6,
    "hmda-masterplan-layer": 0.85
  };

  document.querySelectorAll(".layer-toggle input").forEach(cb => {
    cb.onchange = e => {
      const id = e.target.dataset.layer;
      const targetOpacity = e.target.checked ? (opacities[id] || 1) : 0;

      console.log(`🔄 Layer toggle: ${id}, checked: ${e.target.checked}, opacity: ${targetOpacity}`);

      if (map.getLayer(id)) {
        const type = map.getLayer(id).type;
        console.log(`✅ Layer found: ${id}, type: ${type}`);
        if (type === "fill") map.setPaintProperty(id, "fill-opacity", targetOpacity);
        if (type === "line") map.setPaintProperty(id, "line-opacity", targetOpacity);
        if (type === "symbol") map.setPaintProperty(id, "icon-opacity", targetOpacity);
        if (type === "circle") {
          map.setPaintProperty(id, "circle-opacity", targetOpacity);
          map.setPaintProperty(id, "circle-stroke-opacity", targetOpacity);
        }
        if (type === "raster") map.setPaintProperty(id, "raster-opacity", targetOpacity);
        if (type === "heatmap") map.setPaintProperty(id, "heatmap-opacity", targetOpacity);
      } else {
        console.error(`❌ Layer not found: ${id}`);
      }

      // Special handling for Metro (multi-layer)
      if (id === "metro-layer") {
        const stid = "metro-stations-layer";
        if (map.getLayer(stid)) {
          map.setPaintProperty(stid, "circle-opacity", targetOpacity);
          map.setPaintProperty(stid, "circle-stroke-opacity", targetOpacity);
        }
      }

      // Special handling for multi-layer sources (like Flood/Rainfall)
      if (id === "flood-risk-layer") {
        const subLayers = ["flood-points-layer", "rainfall-layer", "rainfall-labels", "flood-risk-layer"];

        // Toggle Location Markers Visibility to clean up the map
        if (map.getLayer("location-core")) {
          map.setPaintProperty("location-core", "circle-opacity", e.target.checked ? 1 : 1);
          map.setPaintProperty("location-core", "circle-stroke-opacity", e.target.checked ? 1 : 1);
        }

        subLayers.forEach(lyr => {
          if (map.getLayer(lyr)) {
            const type = map.getLayer(lyr).type;
            if (type === "circle") {
              map.setPaintProperty(lyr, "circle-opacity", targetOpacity * 0.9);
              map.setPaintProperty(lyr, "circle-stroke-opacity", targetOpacity * 0.9);
            }
            if (type === "line") map.setPaintProperty(lyr, "line-opacity", targetOpacity * 0.8);
            if (type === "fill") map.setPaintProperty(lyr, "fill-opacity", targetOpacity * 0.6); // Dark layer
            if (type === "symbol") map.setPaintProperty(lyr, "text-opacity", targetOpacity);
          }
        });

        // Show Flood Dashboard on Left if checked
        const card = document.getElementById("intel-card");
        if (e.target.checked) {
          // Move Flood Layers to Top 
          const topLayers = ["flood-risk-layer", "flood-points-layer", "rainfall-layer", "rainfall-labels"];
          topLayers.forEach(lyr => { if (map.getLayer(lyr)) map.moveLayer(lyr); });

          card.style.display = "flex";
          card.innerHTML = `
            <div style="padding: 18px;">
              <div style="margin-bottom: 18px;">
                <h2 class="serif" style="margin: 0; font-size: 1.4rem; color: var(--text-100);">Flood Intelligence</h2>
              </div>
              
              <div style="display: grid; gap: 10px; margin-bottom: 20px;">
                <div style="background: rgba(15, 118, 110, 0.07); border: 1px solid rgba(15, 118, 110, 0.18); padding: 14px; border-radius: 14px;">
                  <div style="font-size: 9px; color: #14B8A6; text-transform: uppercase; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 5px;">Active Alerts</div>
                  <div style="font-size: 1.4rem; font-weight: 800; color: var(--text-100);">148 AWS Stations</div>
                </div>
                <div style="background: rgba(153, 27, 27, 0.07); border: 1px solid rgba(153, 27, 27, 0.18); padding: 14px; border-radius: 14px;">
                  <div style="font-size: 9px; color: #F87171; text-transform: uppercase; font-weight: 700; letter-spacing: 1.5px; margin-bottom: 5px;">Stagnation Points</div>
                  <div style="font-size: 1.4rem; font-weight: 800; color: var(--text-100);">179 GHMC Reports</div>
                </div>
              </div>

              <div style="font-size: 9px; color: var(--text-400); text-transform: uppercase; font-weight: 700; letter-spacing: 2px; margin-bottom: 12px;">Rainfall Legend</div>
              <div style="display: flex; flex-direction: column; gap: 9px;">
                ${[
              { color: '#DC2626', label: 'Extremely Heavy (>204mm)' },
              { color: '#FF6A00', label: 'Very Heavy (115–204mm)' },
              { color: '#16A34A', label: 'Heavy (64–115mm)' },
              { color: '#A2D246', label: 'Moderate (15–64mm)' },
              { color: '#A5D8F3', label: 'Light (2–15mm)' }
            ].map(r => `
                  <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:12px; height:12px; border-radius:50%; background:${r.color}; flex-shrink:0;"></div>
                    <span style="font-size:12px; font-weight:500; color:var(--text-200);">${r.label}</span>
                  </div>`).join('')}
              </div>

              <div style="font-size: 9px; color: var(--text-400); text-transform: uppercase; font-weight: 700; letter-spacing: 2px; margin: 18px 0 10px 0;">Infrastructure</div>
              <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background: #f0abfc; border: 2px solid #c026d3; flex-shrink:0;"></div>
                <span style="font-size: 12px; font-weight: 500; color: var(--text-200);">Water Stagnation (GHMC)</span>
              </div>

              <p style="margin-top: 20px; font-size: 11px; color: var(--text-400); line-height: 1.6; padding: 12px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: 10px;">
                Click any bubble or hydrological line for specific locality insights.
              </p>
            </div>
          `;
        } else {
          card.style.display = "none";
        }
      }
    };
  });



  /* =====================================================
     CLICK → INTEL CARD
  ===================================================== */
  /* =====================================================
     CLICK → INTEL CARD
  ===================================================== */
  /* ===============================
     LOCATION BOUNDARY (OSM DATA)
     OpenFreeMap renders the same OSM data as Nominatim.
     OpenFreeMap's vector tiles store boundaries as LINES (not fill polygons),
     so we fetch the polygon geometry from Nominatim — the identical OSM source.
  =============================== */

  function clearBoundary() {
    if (map.getLayer('location-boundary-fill')) map.removeLayer('location-boundary-fill');
    if (map.getLayer('location-boundary-line')) map.removeLayer('location-boundary-line');
    if (map.getSource('location-boundary')) map.removeSource('location-boundary');
  }

  async function fetchAndShowBoundary(locationName, lat, lng) {
    clearBoundary();
    try {
      let polygon = null;

      // STRATEGY 1: Reverse geocode using the pin's exact coordinates.
      // This is more reliable than name search — we ask OSM "what boundary polygon
      // does this lat/lng fall inside?" and it returns the correct suburb/ward polygon.
      if (lat && lng) {
        const zoom = 14; // suburb-level detail
        const revUrl = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&zoom=${zoom}&format=geojson&polygon_geojson=1`;
        const revRes = await fetch(revUrl, { headers: { 'Accept-Language': 'en' } });
        const revData = await revRes.json();

        if (revData && revData.geometry &&
          (revData.geometry.type === 'Polygon' || revData.geometry.type === 'MultiPolygon')) {
          polygon = revData;
          console.log(`[Boundary] ✓ Reverse geocode found polygon for: ${locationName} (${revData.properties?.display_name})`);
        } else {
          // Reverse returned a point — try one zoom level higher (neighbourhood → suburb level)
          const revUrl2 = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&zoom=${zoom - 1}&format=geojson&polygon_geojson=1`;
          const revRes2 = await fetch(revUrl2, { headers: { 'Accept-Language': 'en' } });
          const revData2 = await revRes2.json();
          if (revData2 && revData2.geometry &&
            (revData2.geometry.type === 'Polygon' || revData2.geometry.type === 'MultiPolygon')) {
            polygon = revData2;
            console.log(`[Boundary] ✓ Reverse geocode (zoom-1) found polygon: ${revData2.properties?.display_name}`);
          }
        }
      }

      // STRATEGY 2: Fallback — name search, pick best polygon result
      if (!polygon) {
        const query = encodeURIComponent(`${locationName}, Hyderabad, Telangana, India`);
        const url = `https://nominatim.openstreetmap.org/search?q=${query}&format=geojson&polygon_geojson=1&limit=5`;
        const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
        const geojson = await res.json();

        if (geojson.features && geojson.features.length > 0) {
          const found = geojson.features.find(
            f => f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon'
          );
          if (found) {
            polygon = found;
            console.log(`[Boundary] ✓ Name search found polygon for: ${locationName}`);
          }
        }
      }

      if (!polygon) {
        console.warn(`[Boundary] No polygon boundary found for: ${locationName}`);
        return;
      }

      map.addSource('location-boundary', { type: 'geojson', data: polygon });

      // Soft onyx-tinted fill
      map.addLayer({
        id: 'location-boundary-fill',
        type: 'fill',
        source: 'location-boundary',
        paint: {
          'fill-color': '#1A1C1E',
          'fill-opacity': 0.04
        }
      }, 'location-core');

      // Refined boundary stroke — Minimal Charcoal
      map.addLayer({
        id: 'location-boundary-line',
        type: 'line',
        source: 'location-boundary',
        paint: {
          'line-color': '#A68A3D',
          'line-width': 1.5,
          'line-opacity': 0.4
        }
      }, 'location-core');

    } catch (err) {
      console.warn(`[Boundary] Could not load boundary for ${locationName}:`, err);
    }
  }

  /* ===============================
     COMMON LOCATION HANDLER
  =============================== */
  async function handleLocationSelect(p) {
    // START CLEANUP: Remove previous amenities, routes, and markers
    clearAmenities();
    clearRoutes();

    // RESET PROPERTIES PANEL: close drawer and clear stale content from previous location
    const propertiesPanel = document.getElementById('properties-panel');
    const detailDrawer = document.getElementById('property-detail-drawer');
    const propList = document.getElementById('prop-list');
    const propLoading = document.getElementById('prop-loading');
    const propPanelCount = document.getElementById('prop-panel-count');

    if (detailDrawer) detailDrawer.classList.remove('open');
    if (propertiesPanel) {
      propertiesPanel.classList.remove('open', 'detail-open');
    }
    if (propList) propList.innerHTML = '';
    if (propLoading) propLoading.style.display = 'none';
    if (propPanelCount) propPanelCount.textContent = '0 projects';

    // Reset navigation state so "Back to Projects" doesn't carry over old data
    window.currentProjectsList = null;
    window.currentProject = null;
    window.currentConfigsList = null;
    window._propertyPinProjects = null;
    // Remove property pins from previous location
    if (map.getLayer('property-pins-layer')) map.removeLayer('property-pins-layer');
    if (map.getLayer('property-pins-labels')) map.removeLayer('property-pins-labels');
    if (map.getSource('property-pins')) map.removeSource('property-pins');
    // END CLEANUP

    const card = document.getElementById("intel-card");
    const emptyState = document.getElementById("empty-state");

    if (emptyState) emptyState.style.display = "none";
    card.style.display = "flex";

    // Reset scroll position to top when new location is selected
    card.scrollTop = 0;

    map.flyTo({
      center: [p.longitude, p.latitude],
      zoom: 13.5,
      pitch: 45,
      bearing: -15,
      duration: 2500,
      essential: true
    });

    // Highlight this locality's boundary fetched directly from OSM (same data as OpenFreeMap)
    fetchAndShowBoundary(p.location, p.latitude, p.longitude);

    const imageName = p.location.toLowerCase().replace(/\s+/g, "_");
    const imagePath = `assets/locations/${imageName}.jpg`;

    // Store current location ID for amenity buttons
    currentLocationId = p.location_id;

    // Fetch intelligence scores with benchmarking
    let intelligenceData = null;
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/intelligence-scores/${p.location_id}`);
      if (response.ok) {
        intelligenceData = await response.json();
      }
    } catch (error) {
      console.warn('Failed to fetch intelligence scores:', error);
    }

    // Use intelligence data (no fallback - must have data)
    const sentimentScore = intelligenceData?.success ? intelligenceData.scores.sentiment.score : 0;
    const growthVal = intelligenceData?.success ? intelligenceData.scores.growth.score : 0;
    const investVal = intelligenceData?.success ? intelligenceData.scores.investment.score : 0;

    // Extract benchmarking data
    const sentimentPercentile = intelligenceData?.scores.sentiment.percentile || null;
    const growthPercentile = intelligenceData?.scores.growth.percentile || null;
    const investPercentile = intelligenceData?.scores.investment.percentile || null;
    
    const cityAvgSentiment = intelligenceData?.scores.sentiment.city_avg || null;
    const cityAvgGrowth = intelligenceData?.scores.growth.city_avg || null;
    const cityAvgInvest = intelligenceData?.scores.investment.city_avg || null;
    
    const sentimentLabel = intelligenceData?.scores.sentiment.label || 'N/A';
    const growthLabel = intelligenceData?.scores.growth.label || 'N/A';
    const investLabel = intelligenceData?.scores.investment.label || 'N/A';

    card.innerHTML = `
      <!-- HERO WITH SMART FALLBACK -->
      <div class="location-hero" id="loc-hero">
        <img
          src="${imagePath}"
          alt="${p.location}"
          onload="this.style.opacity=1"
          onerror="
            this.style.display='none';
            document.getElementById('loc-hero').classList.add('hero-gradient');
          "
          style="opacity:0; transition:opacity 0.4s ease;"
        />
        <div class="location-hero-overlay">
          <div class="location-hero-name">${p.location}</div>
        </div>
      </div>

      <!-- METRICS (3 col) -->
      <!-- MARKET INTELLIGENCE - World-Class Design -->
      <div class="market-intelligence">
        <div class="intelligence-header">
          <h3 class="intelligence-title">Market Intelligence</h3>
          <p class="intelligence-subtitle">AI-powered insights for ${p.location}</p>
        </div>
        
        <div class="metrics-container">
          <!-- Sentiment Metric -->
          <div class="metric-card sentiment-metric" data-metric="sentiment" onclick="expandMetric(this)">
            <div class="metric-compact">
              <div class="metric-icon-wrapper">
                <svg class="metric-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                  <line x1="9" y1="9" x2="9.01" y2="9"/>
                  <line x1="15" y1="9" x2="15.01" y2="9"/>
                </svg>
              </div>
              <div class="metric-data">
                <span class="metric-name">SENTIMENT</span>
                <span class="metric-score">${sentimentScore}<span class="score-suffix">/100</span></span>
                <span class="metric-badge">${sentimentLabel}</span>
              </div>
            </div>
            <div class="metric-expanded">
              ${generateComparisonBar(sentimentScore, cityAvgSentiment, sentimentPercentile)}
              <div class="expanded-content">${formatMarkdownText(p.sentiment_summary) || 'Analyzing community sentiment and market perception...'}</div>
            </div>
          </div>

          <!-- Growth Metric -->
          <div class="metric-card growth-metric" data-metric="growth" onclick="expandMetric(this)">
            <div class="metric-compact">
              <div class="metric-icon-wrapper">
                <svg class="metric-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
                </svg>
              </div>
              <div class="metric-data">
                <span class="metric-name">GROWTH</span>
                <span class="metric-score">${growthVal}<span class="score-suffix">/100</span></span>
                <span class="metric-badge">${growthLabel}</span>
              </div>
            </div>
            <div class="metric-expanded">
              ${generateComparisonBar(growthVal, cityAvgGrowth, growthPercentile)}
              <div class="expanded-content">${formatMarkdownText(p.growth_summary) || 'Evaluating infrastructure development and expansion potential...'}</div>
            </div>
          </div>

          <!-- Investment Metric -->
          <div class="metric-card investment-metric" data-metric="investment" onclick="expandMetric(this)">
            <div class="metric-compact">
              <div class="metric-icon-wrapper">
                <svg class="metric-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                  <line x1="12" y1="1" x2="12" y2="23"/>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </div>
              <div class="metric-data">
                <span class="metric-name">INVESTMENT</span>
                <span class="metric-score">${investVal}<span class="score-suffix">/100</span></span>
                <span class="metric-badge">${investLabel}</span>
              </div>
            </div>
            <div class="metric-expanded">
              ${generateComparisonBar(investVal, cityAvgInvest, investPercentile)}
              <div class="expanded-content">${formatMarkdownText(p.invest_summary) || 'Calculating investment potential and return projections...'}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- PROPERTY COSTS (fetched dynamically) -->
      <div id="property-costs-container">
        <div style="text-align:center; padding:20px; color:var(--text-400); font-size:12px;">
          Loading property costs…
        </div>
      </div>

      <!-- NEARBY AMENITIES -->
      <div class="amenities-section">
        <h4>Nearby Amenities</h4>
        <div class="amenity-grid">
          <button class="amenity-btn" data-amenity="hospitals">
            <span class="btn-icon">🏥</span>
            <span class="btn-label">Hospitals</span>
          </button>
          <button class="amenity-btn" data-amenity="schools">
            <span class="btn-icon">🏫</span>
            <span class="btn-label">Schools</span>
          </button>
          <button class="amenity-btn" data-amenity="malls">
            <span class="btn-icon">🏪</span>
            <span class="btn-label">Malls</span>
          </button>
          <button class="amenity-btn" data-amenity="restaurants">
            <span class="btn-icon">🍽️</span>
            <span class="btn-label">Food</span>
          </button>
          <button class="amenity-btn" data-amenity="banks">
            <span class="btn-icon">🏦</span>
            <span class="btn-label">Banks</span>
          </button>
          <button class="amenity-btn" data-amenity="parks">
            <span class="btn-icon">🏞️</span>
            <span class="btn-label">Parks</span>
          </button>
          <button class="amenity-btn" data-amenity="metro">
            <span class="btn-icon">🚇</span>
            <span class="btn-label">Metro</span>
          </button>
        </div>
        <div style="margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
          <button id="future-insights-btn" class="future-insights-trigger-btn">
            🚀 Future Insights
          </button>
          <button id="clear-amenities-btn" class="clear-btn" style="display:none;">✕ Clear</button>
        </div>
      </div>

      <!-- TRENDS CHARTS - STACKED LAYOUT -->
      <div class="charts-section">
        <!-- Price Trends Chart -->
        <div class="chart-block">
          <div class="chart-header">
            <h4 class="chart-title">📈 Price Trends</h4>
            <span id="price-chart-stat" class="chart-stat">Computing…</span>
          </div>
          <div class="chart-container">
            <canvas id="priceChart"></canvas>
          </div>
        </div>

        <!-- Volume Trends Chart -->
        <div class="chart-block">
          <div class="chart-header">
            <h4 class="chart-title">📊 Volume Trends</h4>
            <span id="volume-chart-stat" class="chart-stat">Computing…</span>
          </div>
          <div class="chart-container">
            <canvas id="volumeChart"></canvas>
          </div>
        </div>
      </div>

      <button id="download-report">⬇ Download Intel Report</button>
    `;

    document.getElementById("download-report").onclick = () => generateReport(p);

    // FUTURE INSIGHTS BUTTON
    const futureInsightsBtn = document.getElementById("future-insights-btn");
    if (futureInsightsBtn) {
      futureInsightsBtn.onclick = () => {
        showFutureInsights(p.location_id, p.location);
      };
    }

    // FETCH AND DISPLAY PROPERTY COSTS DYNAMICALLY
    fetchPropertyCosts(p.location);

    // INITIALIZE BOTH CHARTS SIMULTANEOUSLY
    drawPriceChart(p.location_id);
    drawVolumeChart(p.location);

    if (activeMarker) activeMarker.remove();
    const markerEl = document.createElement('div');
    markerEl.className = 'active-location-marker';
    // Anchor at the center so the pin sits in the middle of the gold circle
    activeMarker = new maplibregl.Marker({ element: markerEl, anchor: 'center' })
      .setLngLat([p.longitude, p.latitude])
      .addTo(map);

    // Initialize map layer tooltips
    setTimeout(() => {
      if (window.tippy) {
        // Only keep layer tooltips, removed metric tooltips
        tippy('.layer-toggle[data-tippy-content]', {
          theme: 'nocturnal',
          placement: 'top',
          animation: 'shift-away',
          delay: [150, 0]
        });
      }
    }, 150);
  }

  map.on("click", "location-core", async e => {
    console.log('Location clicked:', e.features[0].properties);
    const p = e.features[0].properties;

    handleLocationSelect(p);
    // NEW: Also load properties for this location
    loadPropertiesForLocation(p.location);
  });

  map.on('mouseenter', 'location-core', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'location-core', () => {
    map.getCanvas().style.cursor = '';
  });

  /* ===============================
     PROPERTIES PANEL FUNCTIONS
  =============================== */

  function loadPropertiesForLocation(locationName) {
    const panel = document.getElementById('properties-panel');
    const listContainer = document.getElementById('prop-list');
    const loadingEl = document.getElementById('prop-loading');
    const countEl = document.getElementById('prop-panel-count');

    // Track current location for re-renders when RELAI_FILTER arrives later
    window._relaiCurrentLocation = locationName;

    // If parent injected lead-specific properties for this location, use them directly
    const locationKey = (locationName || '').toLowerCase().trim();
    if (window._relaiInjectedByArea && window._relaiInjectedByArea[locationKey]) {
      panel.classList.add('open');
      if (loadingEl) loadingEl.style.display = 'none';
      listContainer.innerHTML = '';
      renderInjectedProperties(window._relaiInjectedByArea[locationKey]);
      return;
    }

    // Open panel and show loading state
    panel.classList.add('open');
    loadingEl.style.display = 'flex';
    listContainer.innerHTML = '';
    countEl.textContent = 'Loading...';

    callSupabaseRPC('get_properties_func', { area_name: locationName, bhk_filter: null })
      .then(properties => {
        loadingEl.style.display = 'none';

        if (!properties || properties.length === 0) {
          listContainer.innerHTML = `
            <div class="prop-empty">
              <div class="prop-empty-icon">🏢</div>
              <p>No properties found in ${locationName}</p>
            </div>
          `;
          countEl.textContent = '0 properties';
          window.allLocationProperties = [];
          return;
        }

        window.allLocationProperties = properties;
        window.currentPropertyIndex = 0;

        // If a lead-specific filter is active (sent from Expert Dashboard), apply it
        // Match by RERA number (primary) or project name (fallback for properties without RERA)
        let displayProperties = properties;
        const hasLeadFilter = (window._relaiFilterReras && window._relaiFilterReras.length > 0) ||
          (window._relaiFilterProjectNames && window._relaiFilterProjectNames.length > 0);
        if (hasLeadFilter) {
          displayProperties = properties.filter(prop => {
            const rera = ((prop.full_details && prop.full_details.rera_number) || '').toLowerCase().trim();
            if (rera && window._relaiFilterReras && window._relaiFilterReras.includes(rera)) return true;
            const name = (prop.projectname || '').toLowerCase().trim();
            if (name && window._relaiFilterProjectNames && window._relaiFilterProjectNames.includes(name)) return true;
            return false;
          });
        }

        // Group by project name AND builder to avoid mixing different projects with same name
        const projectGroups = {};
        displayProperties.forEach(property => {
          const projectKey = `${property.projectname || 'Unnamed Project'}_${property.buildername || 'Unknown Builder'}`;
          if (!projectGroups[projectKey]) {
            projectGroups[projectKey] = {
              projectname: property.projectname || 'Unnamed Project',
              buildername: property.buildername,
              project_type: property.project_type,
              construction_status: property.construction_status,
              areaname: property.areaname,
              images: property.images,
              properties: []
            };
          }
          projectGroups[projectKey].properties.push(property);
        });

        const projects = Object.values(projectGroups)
          .sort((a, b) => b.properties.length - a.properties.length);

        const filterLabel = hasLeadFilter ? ' (lead-matched)' : '';
        countEl.textContent = `${projects.length} project${projects.length !== 1 ? 's' : ''}${filterLabel}`;

        // Render project cards
        projects.forEach(project => {
          const card = createProjectGroupCard(project);
          listContainer.appendChild(card);
        });

        // ── PROPERTY MAP PINS (additive — does not affect panel) ──────────
        // Store projects so pin click handler can look up the right project
        window._propertyPinProjects = projects;

        // Clear any pins from a previous location
        if (map.getLayer('property-pins-layer')) map.removeLayer('property-pins-layer');
        if (map.getLayer('property-pins-labels')) map.removeLayer('property-pins-labels');
        if (map.getSource('property-pins')) map.removeSource('property-pins');

        // Robust bounding box / coordinate extractor
        function extractLatLng(locInfo) {
          if (!locInfo) return null;

          if (typeof locInfo === 'object') {
            if (locInfo.lat !== undefined && locInfo.lng !== undefined) return { lat: parseFloat(locInfo.lat), lng: parseFloat(locInfo.lng) };
            if (locInfo.latitude !== undefined && locInfo.longitude !== undefined) return { lat: parseFloat(locInfo.latitude), lng: parseFloat(locInfo.longitude) };
            return null;
          }

          const str = String(locInfo).trim();

          if (str.startsWith('{')) {
            try {
              const validJson = str.replace(/'/g, '"');
              const parsed = JSON.parse(validJson);
              if (parsed.lat !== undefined && parsed.lng !== undefined) return { lat: parseFloat(parsed.lat), lng: parseFloat(parsed.lng) };
            } catch (e) { }
          }

          const urlMatch = str.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/) || str.match(/(?:q|query)=(-?\d+\.\d+),(-?\d+\.\d+)/);
          if (urlMatch) return { lat: parseFloat(urlMatch[1]), lng: parseFloat(urlMatch[2]) };

          const rawMatch = str.match(/(-?\d+\.\d{3,})\s*,\s*(-?\d+\.\d{3,})/);
          if (rawMatch) return { lat: parseFloat(rawMatch[1]), lng: parseFloat(rawMatch[2]) };

          return null;
        }

        // One GeoJSON feature per project — use first property with valid lat/lng
        const pinFeatures = [];
        projects.forEach((project, idx) => {
          let projectCoords = null;
          // Loop through properties in the project to find the first valid coordinate
          for (const prop of project.properties) {
            projectCoords = extractLatLng(prop.google_place_location) || extractLatLng(prop.google_maps_location);
            if (projectCoords && !isNaN(projectCoords.lat) && !isNaN(projectCoords.lng)) {
              break;
            }
          }

          if (projectCoords && !isNaN(projectCoords.lat) && !isNaN(projectCoords.lng)) {
            pinFeatures.push({
              type: 'Feature',
              geometry: { type: 'Point', coordinates: [projectCoords.lng, projectCoords.lat] },
              properties: {
                project_index: idx,
                projectname: project.projectname,
                buildername: project.buildername || '',
                price_per_sft: project.properties[0].price_per_sft || 0,
                unit_count: project.properties.length
              }
            });
            console.log(`✅ Added pin for ${project.projectname} at [${projectCoords.lng}, ${projectCoords.lat}]`);
          } else {
            console.warn(`⚠️ Could not map ${project.projectname} - no valid coordinates found.`);
          }
        });

        console.log(`📍 Total property pins to display: ${pinFeatures.length} out of ${projects.length} projects`);

        if (pinFeatures.length > 0) {
          map.addSource('property-pins', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: pinFeatures }
          });

          // Royal Indigo circle for property pins - sleek & premium
          map.addLayer({
            id: 'property-pins-layer',
            type: 'circle',
            source: 'property-pins',
            paint: {
              'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 4, 15, 10],
              'circle-color': '#f40000ff', // Royal Indigo
              'circle-stroke-color': '#FFFFFF',
              'circle-stroke-width': 2,
              'circle-opacity': 0.95
            }
          });

          // Project name label above each pin
          map.addLayer({
            id: 'property-pins-labels',
            type: 'symbol',
            source: 'property-pins',
            layout: {
              'text-field': ['get', 'projectname'],
              'text-size': 11,
              'text-offset': [0, -1.8],
              'text-anchor': 'bottom',
              'text-font': ['Noto Sans Bold'],
              'text-allow-overlap': false,
              'text-optional': true
            },
            paint: {
              'text-color': '#FFFFFF',
              'text-halo-color': '#f40000ff',
              'text-halo-width': 2,
              'text-halo-blur': 1
            }
          });

          // Click pin → open that project's full detail in the already-open panel
          map.on('click', 'property-pins-layer', (e) => {
            const pinProps = e.features[0].properties;
            const proj = (window._propertyPinProjects || [])[pinProps.project_index];
            if (!proj) return;

            // Store current list for back navigation BEFORE clearing
            if (!window.currentProjectsList && listContainer.children.length > 0) {
              window.currentProjectsList = Array.from(listContainer.children);
            }

            // Clear list and show this project's detail
            listContainer.innerHTML = '';
            showProjectConfigurations(proj);
          });

          map.on('mouseenter', 'property-pins-layer', () => {
            map.getCanvas().style.cursor = 'pointer';
          });
          map.on('mouseleave', 'property-pins-layer', () => {
            map.getCanvas().style.cursor = '';
          });
        }
        // ── END PROPERTY MAP PINS ──────────────────────────────────────────
      })
      .catch(err => {
        console.error('Properties fetch error:', err);
        loadingEl.style.display = 'none';
        window.allLocationProperties = [];
        listContainer.innerHTML = `
          <div class="prop-empty">
            <div class="prop-empty-icon">⚠️</div>
            <p>Failed to load properties. Please try again.</p>
          </div>
        `;
      });
  }



  function openPropertyDetailWithConfigs(proj) {
    const drawer = document.getElementById('property-detail-drawer');
    const panel = document.getElementById('properties-panel');

    // Show drawer
    drawer.classList.add('open');
    panel.classList.add('detail-open');

    // If only one config, use the simple view
    if (!proj.allConfigs || proj.allConfigs.length === 1) {
      openPropertyDetail(proj.id);
      return;
    }

    // Multiple configs - fetch FULL details first, then show tabs
    drawer.innerHTML = `
      <div class="detail-header">
        <button class="detail-back-btn" id="detail-back-btn">← Back</button>
        <button class="detail-close-btn" id="detail-close-btn">✕</button>
      </div>
      <div style="display:flex; align-items:center; justify-content:center; padding:60px 20px;">
        <div class="prop-spinner"></div>
        <span style="margin-left:12px; color:var(--t3);">Loading details...</span>
      </div>
    `;

    // Fetch full property details
    callSupabaseRPC('get_property_by_id_func', { prop_id: proj.id })
      .then(data => {
        // Handle Supabase RPC response format (returns array)
        const fullProp = Array.isArray(data) && data.length > 0 ? data[0] : data;
        // Merge full details with the grouped configs
        const enrichedProj = {
          ...fullProp,
          allConfigs: proj.allConfigs,
          bhkTypes: proj.bhkTypes,
          configCount: proj.configCount
        };
        renderPropertyDetailWithTabs(enrichedProj);
      })
      .catch(err => {
        console.error('Property detail fetch error:', err);
        drawer.innerHTML = `
          <div class="detail-header">
            <button class="detail-back-btn" id="detail-back-btn">← Back</button>
            <button class="detail-close-btn" id="detail-close-btn">✕</button>
          </div>
          <div style="padding:40px 20px; text-align:center; color:var(--t3);">
            <p>Failed to load property details.</p>
          </div>
        `;
      });
  }

  function renderPropertyDetailWithTabs(proj) {
    const drawer = document.getElementById('property-detail-drawer');
    const configs = proj.allConfigs;

    // Parse images from first config
    let images = [];
    if (configs[0].images) {
      try {
        images = JSON.parse(configs[0].images);
        if (!Array.isArray(images)) images = [];
      } catch (e) {
        images = [];
      }
    }

    // Build gallery HTML
    let galleryHTML = '';
    if (images.length > 0) {
      galleryHTML = images.map(img => `<img src="${img}" alt="${proj.projectname}" />`).join('');
    } else {
      galleryHTML = '<div class="detail-gallery-placeholder">🏢</div>';
    }

    // Build badges
    let badgesHTML = '';
    if (proj.project_type) badgesHTML += `<span class="detail-badge detail-badge-type">${proj.project_type}</span>`;
    if (proj.city) badgesHTML += `<span class="detail-badge detail-badge-city">${proj.city}</span>`;
    if (proj.construction_status) badgesHTML += `<span class="detail-badge detail-badge-status">${proj.construction_status}</span>`;

    // Build configuration tabs
    const tabsHTML = configs.map((config, idx) => `
      <button class="config-tab ${idx === 0 ? 'active' : ''}" data-config-idx="${idx}">
        ${config.bhk || 'Config ' + (idx + 1)}
      </button>
    `).join('');

    // Build configuration content
    const configContentsHTML = configs.map((config, idx) => {
      const keyStats = `
        <div class="detail-stat-box">
          <span class="detail-stat-val">${config.bhk || 'N/A'}</span>
          <span class="detail-stat-lbl">BHK</span>
        </div>
        <div class="detail-stat-box">
          <span class="detail-stat-val">${config.sqfeet ? config.sqfeet.toLocaleString() : 'N/A'}</span>
          <span class="detail-stat-lbl">Sqft</span>
        </div>
        <div class="detail-stat-box">
          <span class="detail-stat-val">${config.price_per_sft ? '₹' + config.price_per_sft.toLocaleString() : 'N/A'}</span>
          <span class="detail-stat-lbl">Per Sqft</span>
        </div>
      `;

      return `
        <div class="config-content ${idx === 0 ? 'active' : ''}" data-config-idx="${idx}">
          <div class="detail-key-stats">${keyStats}</div>
          
          <div class="detail-sections">
            ${buildDetailSection('💰 Pricing', [
        { label: 'Base Price', value: config.baseprojectprice ? `₹${(config.baseprojectprice / 10000000).toFixed(2)} Cr` : null },
        { label: 'Price / sqft', value: config.price_per_sft ? `₹${config.price_per_sft.toLocaleString()}` : null },
        { label: 'Total Buildup Area', value: config.total_buildup_area ? `${config.total_buildup_area} sqft` : null },
        { label: 'Price Last Updated', value: config.price_per_sft_update_date },
        { label: 'Floor Rise Charges', value: config.floor_rise_charges },
        { label: 'Floor Rise ₹/floor', value: config.floor_rise_amount_per_floor },
        { label: 'Applicable Above Floor No', value: config.floor_rise_applicable_above_floor_no },
        { label: 'Facing Charges', value: config.facing_charges },
        { label: 'PLC', value: config.preferential_location_charges },
        { label: 'PLC Conditions', value: config.preferential_location_charges_conditions, span: true },
        { label: 'Extra Parking Cost', value: config.amount_for_extra_car_parking }
      ])}
            
            ${buildDetailSection('🛏️ Unit Configuration', [
        { label: 'BHK Config', value: config.bhk },
        { label: 'Area (sqft)', value: config.sqfeet },
        { label: 'Area (sqyard)', value: config.sqyard },
        { label: 'Facing', value: config.facing },
        { label: 'Car Parkings', value: config.no_of_car_parkings }
      ])}
          </div>
        </div>
      `;
    }).join('');

    drawer.innerHTML = `
      <div class="detail-header">
        <button class="detail-back-btn" id="detail-back-btn">← Back</button>
        <button class="detail-close-btn" id="detail-close-btn">✕</button>
      </div>
      
      <div class="detail-scrollable">
        <div class="detail-gallery">${galleryHTML}</div>
        
        <div class="detail-hero">
          <div class="detail-badges">${badgesHTML}</div>
          <h2 class="detail-proj-name">${proj.projectname || 'Unnamed Project'}</h2>
          <p class="detail-builder">${proj.buildername || 'Builder not specified'}</p>
          ${proj.latitude && proj.longitude ? `
          <button class="calculate-commute-btn" onclick='openCommuteCalculator(${proj.latitude}, ${proj.longitude}, "${(proj.projectname || '').replace(/"/g, '&quot;')}")'>
            🚗 Calculate Commute
          </button>
          ` : ''}
        </div>
        
        <div class="config-tabs-container">
          <div class="config-tabs">${tabsHTML}</div>
        </div>
        
        <div class="config-contents-wrapper">${configContentsHTML}</div>
        
        <div class="detail-sections-common">
          ${buildDetailSection('🏠 Basic Info', [
      { label: 'Project Name', value: proj.projectname },
      { label: 'Builder', value: proj.buildername },
      { label: 'Type', value: proj.project_type },
      { label: 'Community', value: proj.communitytype },
      { label: 'Status', value: proj.status },
      { label: 'Project Status', value: proj.project_status },
      { label: 'Availability', value: proj.isavailable }
    ])}
          
          ${buildDetailSection('📍 Location', [
      { label: 'Area', value: proj.areaname },
      { label: 'Location', value: proj.projectlocation },
      { label: 'Google Name', value: proj.google_place_name },
      { label: 'Full Address', value: proj.google_place_address, span: true },
      { label: 'Maps Link', value: proj.google_maps_location, link: true },
      { label: 'Open in Maps', value: proj.mobile_google_map_url, link: true }
    ])}
          
          ${buildDetailSection('🏗️ Project Details', [
      { label: 'Launch Date', value: proj.project_launch_date },
      { label: 'Possession Date', value: proj.possession_date },
      { label: 'Construction Status', value: proj.construction_status },
      { label: 'Material', value: proj.construction_material },
      { label: 'Land Area', value: proj.total_land_area ? `${proj.total_land_area} sqft` : null },
      { label: 'Towers', value: proj.number_of_towers },
      { label: 'Floors', value: proj.number_of_floors },
      { label: 'Flats/Floor', value: proj.number_of_flats_per_floor },
      { label: 'Total Sizes', value: proj.total_number_of_units },
      { label: 'Open Space %', value: proj.open_space },
      { label: 'Carpet Area %', value: proj.carpet_area_percentage },
      { label: 'Floor-to-Ceiling Height', value: proj.floor_to_ceiling_height }
    ])}
          
          ${buildDetailSection('🏊 Amenities & Specs', [
      { label: 'External Amenities', value: proj.external_amenities, span: true },
      { label: 'Specifications', value: proj.specification, span: true },
      { label: 'Power Backup', value: proj.powerbackup },
      { label: 'Passenger Lifts', value: proj.no_of_passenger_lift },
      { label: 'Service Lifts', value: proj.no_of_service_lift },
      { label: 'Visitor Parking', value: proj.visitor_parking },
      { label: 'Ground Vehicle Movement', value: proj.ground_vehicle_movement },
      { label: 'Main Door Height', value: proj.main_door_height },
      { label: 'Home Loan', value: proj.home_loan },
      { label: 'Banks for Loan', value: proj.available_banks_for_loan, span: true }
    ])}
          
          ${buildDetailSection('👷 Builder Profile', [
      { label: 'Years in Business', value: proj.builder_age },
      { label: 'Completed Projects', value: proj.builder_completed_properties },
      { label: 'Ongoing Projects', value: proj.builder_ongoing_projects },
      { label: 'Upcoming Projects', value: proj.builder_upcoming_properties },
      { label: 'Total Projects', value: proj.builder_total_properties },
      { label: 'Operating Cities', value: proj.builder_operating_locations },
      { label: 'Headquarters', value: proj.builder_origin_city }
    ])}
        </div>
      </div>
    `;

    // Add tab click handlers
    drawer.querySelectorAll('.config-tab').forEach(tab => {
      tab.onclick = () => {
        const idx = tab.dataset.configIdx;

        // Update active tab
        drawer.querySelectorAll('.config-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update active content
        drawer.querySelectorAll('.config-content').forEach(c => c.classList.remove('active'));
        drawer.querySelector(`.config-content[data-config-idx="${idx}"]`).classList.add('active');
      };
    });
  }

  function openPropertyDetail(propertyId) {
    const drawer = document.getElementById('property-detail-drawer');
    const panel = document.getElementById('properties-panel');

    // Show drawer
    drawer.classList.add('open');
    panel.classList.add('detail-open');

    // Show loading state
    drawer.innerHTML = `
      <div class="detail-header">
        <button class="detail-back-btn" id="detail-back-btn">← Back</button>
        <button class="detail-close-btn" id="detail-close-btn">✕</button>
      </div>
      <div style="display:flex; align-items:center; justify-content:center; padding:60px 20px;">
        <div class="prop-spinner"></div>
        <span style="margin-left:12px; color:var(--t3);">Loading details...</span>
      </div>
    `;

    // Fetch full property details
    callSupabaseRPC('get_property_by_id_func', { prop_id: propertyId })
      .then(data => {
        // Handle Supabase RPC response format (returns array)
        const prop = Array.isArray(data) && data.length > 0 ? data[0] : data;
        renderPropertyDetail(prop);
      })
      .catch(err => {
        console.error('Property detail fetch error:', err);
        drawer.innerHTML = `
          <div class="detail-header">
            <button class="detail-back-btn" id="detail-back-btn">← Back</button>
            <button class="detail-close-btn" id="detail-close-btn">✕</button>
          </div>
          <div style="padding:40px 20px; text-align:center; color:var(--t3);">
            <p>Failed to load property details.</p>
          </div>
        `;
      });
  }

  function renderPropertyDetail(prop) {
    const drawer = document.getElementById('property-detail-drawer');

    // Parse images
    let images = [];
    if (prop.images) {
      try {
        images = JSON.parse(prop.images);
        if (!Array.isArray(images)) images = [];
      } catch (e) {
        images = [];
      }
    }

    // Build gallery HTML
    let galleryHTML = '';
    if (images.length > 0) {
      galleryHTML = images.map(img => `<img src="${img}" alt="${prop.projectname}" />`).join('');
    } else {
      galleryHTML = '<div class="detail-gallery-placeholder">🏢</div>';
    }

    // Build badges
    let badgesHTML = '';
    if (prop.project_type) badgesHTML += `<span class="detail-badge detail-badge-type">${prop.project_type}</span>`;
    if (prop.city) badgesHTML += `<span class="detail-badge detail-badge-city">${prop.city}</span>`;
    if (prop.construction_status) badgesHTML += `<span class="detail-badge detail-badge-status">${prop.construction_status}</span>`;

    // Key stats
    const keyStats = `
      <div class="detail-stat-box">
        <span class="detail-stat-val">${prop.bhk || 'N/A'}</span>
        <span class="detail-stat-lbl">BHK</span>
      </div>
      <div class="detail-stat-box">
        <span class="detail-stat-val">${prop.sqfeet ? prop.sqfeet.toLocaleString() : 'N/A'}</span>
        <span class="detail-stat-lbl">Sqft</span>
      </div>
      <div class="detail-stat-box">
        <span class="detail-stat-val">${prop.price_per_sft ? '₹' + prop.price_per_sft.toLocaleString() : 'N/A'}</span>
        <span class="detail-stat-lbl">Per Sqft</span>
      </div>
    `;

    drawer.innerHTML = `
      <div class="detail-header">
        <button class="detail-back-btn" id="detail-back-btn">← Back</button>
        <button class="detail-close-btn" id="detail-close-btn">✕</button>
      </div>
      
      <div class="detail-scrollable">
        <div class="detail-gallery">${galleryHTML}</div>
        
        <div class="detail-hero">
          <div class="detail-badges">${badgesHTML}</div>
          <h2 class="detail-proj-name">${prop.projectname || 'Unnamed Project'}</h2>
          <p class="detail-builder">${prop.buildername || 'Builder not specified'}</p>
          <div class="detail-key-stats">${keyStats}</div>
        </div>
        
        ${prop.latitude && prop.longitude ? `
        <div class="detail-section commute-calc-section">
          <h3 class="detail-section-title">🚗 Commute Calculator</h3>
          <div class="commute-search-box-detail">
            <input 
              type="text" 
              id="office-search-detail-${prop.id}" 
              class="office-search-input-detail" 
              placeholder="Search for your office location..." 
              autocomplete="off"
              data-prop-lat="${prop.latitude}"
              data-prop-lng="${prop.longitude}"
              data-prop-name="${(prop.projectname || '').replace(/"/g, '&quot;')}"
            />
            <div id="office-suggestions-detail-${prop.id}" class="office-suggestions-detail"></div>
          </div>
          <div id="commute-routes-detail-${prop.id}" class="commute-routes-detail" style="display: none;">
            <div class="route-cards-detail"></div>
          </div>
        </div>
        ` : ''}
        
        <div class="detail-sections">
          ${buildDetailSection('🏠 Basic Info', [
      { label: 'Project Name', value: prop.projectname },
      { label: 'Builder', value: prop.buildername },
      { label: 'Type', value: prop.project_type },
      { label: 'Community', value: prop.communitytype },
      { label: 'Status', value: prop.status },
      { label: 'Project Status', value: prop.project_status },
      { label: 'Availability', value: prop.isavailable }
    ])}
          
          ${buildDetailSection('📍 Location', [
      { label: 'Area', value: prop.areaname },
      { label: 'Location', value: prop.projectlocation },
      { label: 'Google Name', value: prop.google_place_name },
      { label: 'Full Address', value: prop.google_place_address, span: true },
      { label: 'Maps Link', value: prop.google_maps_location, link: true },
      { label: 'Open in Maps', value: prop.mobile_google_map_url, link: true }
    ])}
          
          ${buildDetailSection('💰 Pricing', [
      { label: 'Base Price', value: prop.baseprojectprice ? `₹${(prop.baseprojectprice / 10000000).toFixed(2)} Cr` : null },
      { label: 'Price / sqft', value: prop.price_per_sft ? `₹${prop.price_per_sft.toLocaleString()}` : null },
      { label: 'Total Buildup Area', value: prop.total_buildup_area ? `${prop.total_buildup_area} sqft` : null },
      { label: 'Price Last Updated', value: prop.price_per_sft_update_date },
      { label: 'Floor Rise Charges', value: prop.floor_rise_charges },
      { label: 'Floor Rise ₹/floor', value: prop.floor_rise_amount_per_floor },
      { label: 'Applicable Above Floor No', value: prop.floor_rise_applicable_above_floor_no },
      { label: 'Facing Charges', value: prop.facing_charges },
      { label: 'PLC', value: prop.preferential_location_charges },
      { label: 'PLC Conditions', value: prop.preferential_location_charges_conditions, span: true },
      { label: 'Extra Parking Cost', value: prop.amount_for_extra_car_parking }
    ])}
          
          ${buildDetailSection('🏗️ Project Details', [
      { label: 'Launch Date', value: prop.project_launch_date },
      { label: 'Possession Date', value: prop.possession_date },
      { label: 'Construction Status', value: prop.construction_status },
      { label: 'Material', value: prop.construction_material },
      { label: 'Land Area', value: prop.total_land_area ? `${prop.total_land_area} sqft` : null },
      { label: 'Towers', value: prop.number_of_towers },
      { label: 'Floors', value: prop.number_of_floors },
      { label: 'Flats/Floor', value: prop.number_of_flats_per_floor },
      { label: 'Total Sizes', value: prop.total_number_of_units },
      { label: 'Open Space %', value: prop.open_space },
      { label: 'Carpet Area %', value: prop.carpet_area_percentage },
      { label: 'Floor-to-Ceiling Height', value: prop.floor_to_ceiling_height }
    ])}
          
          ${buildDetailSection('🛏️ Unit Configuration', [
      { label: 'BHK Config', value: prop.bhk },
      { label: 'Area (sqft)', value: prop.sqfeet },
      { label: 'Area (sqyard)', value: prop.sqyard },
      { label: 'Facing', value: prop.facing },
      { label: 'Car Parkings', value: prop.no_of_car_parkings }
    ])}
          
          ${buildDetailSection('🏊 Amenities & Specs', [
      { label: 'External Amenities', value: prop.external_amenities, span: true },
      { label: 'Specifications', value: prop.specification, span: true },
      { label: 'Power Backup', value: prop.powerbackup },
      { label: 'Passenger Lifts', value: prop.no_of_passenger_lift },
      { label: 'Service Lifts', value: prop.no_of_service_lift },
      { label: 'Visitor Parking', value: prop.visitor_parking },
      { label: 'Ground Vehicle Movement', value: prop.ground_vehicle_movement },
      { label: 'Main Door Height', value: prop.main_door_height },
      { label: 'Home Loan', value: prop.home_loan },
      { label: 'Banks for Loan', value: prop.available_banks_for_loan, span: true }
    ])}
          
          ${buildDetailSection('👷 Builder Profile', [
      { label: 'Years in Business', value: prop.builder_age },
      { label: 'Completed Projects', value: prop.builder_completed_properties },
      { label: 'Ongoing Projects', value: prop.builder_ongoing_projects },
      { label: 'Upcoming Projects', value: prop.builder_upcoming_properties },
      { label: 'Total Projects', value: prop.builder_total_properties },
      { label: 'Operating Cities', value: prop.builder_operating_locations },
      { label: 'Headquarters', value: prop.builder_origin_city }
    ])}
        </div>
      </div>
    `;
  }

  function buildDetailSection(title, fields) {
    // Debug logging
    console.log(`Building section: ${title}`, fields);

    const validFields = fields.filter(f => f.value && f.value !== 'null' && f.value !== 'N/A' && f.value !== 'None');
    console.log(`Valid fields for ${title}:`, validFields);

    if (validFields.length === 0) return ''; // Don't show empty sections

    const rowsHTML = validFields.map(f => {
      if (f.link && f.value) {
        return `
          <div class="detail-row ${f.span ? 'single' : ''}">
            <div class="detail-row-label">${f.label}</div>
            <div class="detail-row-value link"><a href="${f.value}" target="_blank" rel="noopener noreferrer">Open in Maps</a></div>
          </div>
        `;
      }
      return `
        <div class="detail-row ${f.span ? 'single' : ''}">
          <div class="detail-row-label">${f.label}</div>
          <div class="detail-row-value">${f.value || 'Not available'}</div>
        </div>
      `;
    }).join('');

    return `
      <div class="detail-section">
        <h3 class="detail-section-title">${title}</h3>
        <div class="detail-rows ${validFields.length === 1 || validFields.some(f => f.span) ? 'single' : ''}">${rowsHTML}</div>
      </div>
    `;
  }

  // Event listeners for panel controls
  document.addEventListener('click', (e) => {
    // Close properties panel
    if (e.target.closest('#close-properties-panel')) {
      document.getElementById('properties-panel').classList.remove('open');
      document.getElementById('property-detail-drawer').classList.remove('open');
      document.getElementById('properties-panel').classList.remove('detail-open');
    }

    // Back button in detail drawer
    if (e.target.closest('#detail-back-btn')) {
      document.getElementById('property-detail-drawer').classList.remove('open');
      document.getElementById('properties-panel').classList.remove('detail-open');
    }

    // Close button in detail drawer
    if (e.target.closest('#detail-close-btn')) {
      document.getElementById('property-detail-drawer').classList.remove('open');
      document.getElementById('properties-panel').classList.remove('detail-open');
    }
  });

  // METRO LAYER CLICK HANDLER
  map.on("click", "metro-layer", e => {
    if (currentPopup) currentPopup.remove();
    const coordinates = e.lngLat;
    currentPopup = new maplibregl.Popup({ closeButton: true, closeOnClick: true })
      .setLngLat(coordinates)
      .setHTML(`
        <div style="padding:4px 2px;">
          <div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--gold);margin-bottom:5px;">🚇 Metro Rail</div>
          <div style="font-size:0.95rem;font-weight:600;color:var(--text-100);">Hyderabad Metro Rail</div>
          <div style="font-size:0.72rem;color:var(--text-300);margin-top:4px;">Red · Blue · Green Lines</div>
        </div>
      `)
      .addTo(map);
  });
  map.on('mouseenter', 'metro-layer', () => { map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', 'metro-layer', () => { map.getCanvas().style.cursor = ''; });

  // ORR LAYER CLICK HANDLER
  map.on("click", "orr-layer", e => {
    if (currentPopup) currentPopup.remove();
    const coordinates = e.lngLat;
    currentPopup = new maplibregl.Popup({ closeButton: true, closeOnClick: true })
      .setLngLat(coordinates)
      .setHTML(`
        <div style="padding:4px 2px;">
          <div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--gold);margin-bottom:5px;">🛣️ Infrastructure</div>
          <div style="font-size:0.95rem;font-weight:600;color:var(--text-100);">Nehru Outer Ring Road</div>
          <div style="font-size:0.72rem;color:var(--text-300);margin-top:5px;line-height:1.5;">158 km circular expressway · Key to suburban growth</div>
        </div>
      `)
      .addTo(map);
  });
  map.on('mouseleave', 'orr-layer', () => { map.getCanvas().style.cursor = ''; });



  // --- ADVANCED CHART.JS PLUGINS ---

  // 1. Vertical Crosshair Plugin
  // Draws a sleek vertical dotted line aligned with the cursor
  const crosshairPlugin = {
    id: 'crosshairLine',
    afterDraw: chart => {
      if (chart.tooltip && chart.tooltip._active && chart.tooltip._active.length) {
        const activePoint = chart.tooltip._active[0];
        const ctx = chart.ctx;
        const x = activePoint.element.x;
        const topY = chart.scales.y.top;
        const bottomY = chart.scales.y.bottom;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(x, topY);
        ctx.lineTo(x, bottomY);
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
        ctx.setLineDash([4, 4]); // Dashboard style dotted line
        ctx.stroke();
        ctx.restore();
      }
    }
  };

  // 2. Glowing Line Shadow Plugin
  // Adds a native canvas drop-shadow that makes a line look like glowing neon
  const glowingLinePlugin = {
    id: 'glowingLine',
    beforeDatasetsDraw: chart => {
      if (chart.config.type !== 'line') return;
      const ctx = chart.ctx;
      ctx.save();
      // Drop shadow configuration
      ctx.shadowColor = 'rgba(255, 215, 0, 0.6)'; // Gold glow
      ctx.shadowBlur = 12;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 4;
    },
    afterDatasetsDraw: chart => {
      chart.ctx.restore();
    }
  };

  // Register globally so all charts get the crosshair tracking
  if (window.Chart) {
    Chart.register(crosshairPlugin, glowingLinePlugin);
  }

  // CHART.JS HELPER - Dual Charts Display
  let priceChartInstance = null; // Store price chart instance
  let volumeChartInstance = null; // Store volume chart instance

  function drawPriceChart(locationId) {
    console.log('Drawing price chart for location ID:', locationId);

    callSupabaseRPC('get_location_trends_func', { loc_id: locationId })
      .then(data => {
        // Handle the different response format from Supabase RPC
        const result = Array.isArray(data) && data.length > 0 ? data[0] : data;
        console.log('Price trends data received:', result);

        // Handle new API response structure
        if (!result || result.error || !result.trends || result.trends.length === 0) {
          console.warn('No chart data available:', result?.error || 'No trends data');
          document.getElementById('price-chart-stat').style.display = 'none';

          // Show "No data" message in chart area
          const chartContainer = document.querySelector('#priceChart').parentElement;
          if (chartContainer) {
            chartContainer.innerHTML = '<div style="display:flex; align-items:center; justify-content:center; height:100%; color:#999; font-size:11px; font-family:Outfit;">No price trend data available</div>';
          }
          return;
        }

        const trendsData = result.trends;
        const cagr = result.cagr || 0;
        const growthYoy = result.growth_yoy || 0;

        console.log('Rendering price chart with', trendsData.length, 'data points');

        // Update CAGR stat with enhanced styling
        const statElement = document.getElementById('price-chart-stat');
        if (cagr !== 0) {
          const cagrColor = cagr > 10 ? '#4CAF50' : cagr > 5 ? '#FFA726' : '#A68A3D';
          const trendIcon = cagr > 0 ? '↗' : '↘';
          statElement.innerHTML = `${trendIcon} <span style="color:${cagrColor}; font-weight:800;">${cagr.toFixed(1)}%</span> CAGR`;
          statElement.style.display = 'block';
        } else {
          statElement.style.display = 'none';
        }

        // Destroy existing chart instance if it exists
        if (priceChartInstance) {
          priceChartInstance.destroy();
        }

        const canvas = document.getElementById('priceChart');
        if (!canvas) {
          console.error('Price canvas element not found!');
          return;
        }

        const ctx = canvas.getContext('2d');

        // Enhanced Emerald Green gradient for Price Trend
        const gradient = ctx.createLinearGradient(0, 0, 0, 140);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.35)'); // Emerald Green
        gradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.15)');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');

        // Create glow effect gradient for line
        const glowGradient = ctx.createLinearGradient(0, 0, 0, 140);
        glowGradient.addColorStop(0, '#34D399'); // Light Emerald
        glowGradient.addColorStop(0.5, '#10B981'); // Standard Emerald
        glowGradient.addColorStop(1, '#059669'); // Dark Emerald

        priceChartInstance = new Chart(ctx, {
          type: 'line',
          data: {
            labels: trendsData.map(d => d.year),
            datasets: [{
              label: 'Price per SqFt',
              data: trendsData.map(d => d.price),
              borderColor: glowGradient,
              borderWidth: 3,
              fill: true,
              backgroundColor: gradient,
              tension: 0.45,
              // Clean Premium Point Styling
              pointStyle: 'circle',
              pointRadius: 3.5,
              pointHoverRadius: 6,
              pointBackgroundColor: '#FFFFFF',
              pointBorderColor: '#059669', // Emerald
              pointBorderWidth: 2,
              pointHoverBackgroundColor: '#059669',
              pointHoverBorderColor: '#FFFFFF',
              pointHoverBorderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index',
              intersect: false
            },
            animations: {
              x: {
                type: 'number',
                easing: 'linear',
                duration: 1500 / Math.max(1, trendsData.length),
                from: NaN,
                delay(ctx) {
                  if (ctx.type !== 'data' || ctx.xStarted) {
                    return 0;
                  }
                  ctx.xStarted = true;
                  return ctx.index * (1500 / Math.max(1, trendsData.length));
                }
              },
              y: {
                type: 'number',
                easing: 'linear',
                duration: 1500 / Math.max(1, trendsData.length),
                from(ctx) {
                  if (ctx.index === 0) {
                    return ctx.chart.scales.y.getPixelForValue(trendsData[0].price);
                  }
                  const meta = ctx.chart.getDatasetMeta(ctx.datasetIndex);
                  return meta.data[ctx.index - 1] ? meta.data[ctx.index - 1].getProps(['y'], true).y : ctx.chart.scales.y.getPixelForValue(trendsData[ctx.index].price);
                },
                delay(ctx) {
                  if (ctx.type !== 'data' || ctx.yStarted) {
                    return 0;
                  }
                  ctx.yStarted = true;
                  return ctx.index * (1500 / Math.max(1, trendsData.length));
                }
              }
            },
            plugins: {
              legend: { display: false },
              tooltip: {
                enabled: true,
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(15, 23, 42, 0.9)', // Match Nocturnal Theme
                borderColor: 'rgba(16, 185, 129, 0.3)', // Emerald border
                borderWidth: 1,
                titleColor: '#34D399', // Light emerald
                bodyColor: '#e2e2e8',
                titleFont: {
                  family: 'Outfit',
                  weight: '700',
                  size: 12
                },
                bodyFont: {
                  family: 'Inter',
                  size: 11,
                  weight: '500'
                },
                padding: 12,
                cornerRadius: 8,
                caretSize: 6,
                displayColors: false,
                callbacks: {
                  title: (context) => {
                    return `Year ${context[0].label}`;
                  },
                  label: (context) => {
                    const price = context.parsed.y;
                    const index = context.dataIndex;

                    // Calculate YoY change if not first point
                    let changeText = '';
                    if (index > 0) {
                      const prevPrice = trendsData[index - 1].price;
                      const change = ((price - prevPrice) / prevPrice * 100).toFixed(1);
                      const changeIcon = change > 0 ? '↑' : '↓';
                      changeText = ` (${changeIcon}${Math.abs(change)}% YoY)`;
                    }

                    return `Price: ₹${price.toLocaleString()}/sqft${changeText}`;
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  display: true,
                  color: 'rgba(16, 185, 129, 0.05)',
                  lineWidth: 1
                },
                ticks: {
                  color: '#9E9E9E',
                  font: {
                    family: 'Outfit',
                    size: 9,
                    weight: '600'
                  },
                  padding: 4
                },
                border: {
                  color: 'rgba(16, 185, 129, 0.2)'
                }
              },
              y: {
                grid: {
                  color: 'rgba(16, 185, 129, 0.08)',
                  lineWidth: 1
                },
                ticks: {
                  color: '#9E9E9E',
                  font: {
                    family: 'Outfit',
                    size: 9,
                    weight: '600'
                  },
                  padding: 4,
                  callback: (v) => {
                    if (v >= 1000) {
                      return '₹' + (v / 1000).toFixed(1) + 'k';
                    }
                    return '₹' + v;
                  }
                },
                border: {
                  color: 'rgba(166, 138, 61, 0.2)'
                }
              }
            }
          }
        });

        console.log('Price chart created successfully:', priceChartInstance);
      })
      .catch(err => {
        console.error("Price Chart Fetch Error:", err);
        document.getElementById('price-chart-stat').style.display = 'none';
        const chartContainer = document.querySelector('#priceChart').parentElement;
        if (chartContainer) {
          chartContainer.innerHTML = '<div style="display:flex; align-items:center; justify-content:center; height:100%; color:#ff5555; font-size:11px; font-family:Outfit;">Error loading price data</div>';
        }
      });
  }

  function drawVolumeChart(locationName) {
    console.log('Drawing volume chart for location:', locationName);

    // Check if volume data exists for this location
    if (!window.VOLUME_TRENDS_DATA || !window.VOLUME_TRENDS_DATA[locationName]) {
      console.warn('No volume data available for:', locationName);
      document.getElementById('volume-chart-stat').style.display = 'none';

      const chartContainer = document.querySelector('#volumeChart').parentElement;
      if (chartContainer) {
        chartContainer.innerHTML = '<div style="display:flex; align-items:center; justify-content:center; height:100%; color:#999; font-size:11px; font-family:Outfit;">No volume trend data available</div>';
      }
      return;
    }

    const volumeData = window.VOLUME_TRENDS_DATA[locationName];
    console.log('Rendering volume chart with data:', volumeData);

    // Calculate comprehensive volume statistics
    const volumes = volumeData.volumes;
    const years = volumeData.years;

    // Find peak and trough
    const maxVolume = Math.max(...volumes);
    const minVolume = Math.min(...volumes);
    const maxIndex = volumes.indexOf(maxVolume);
    const minIndex = volumes.indexOf(minVolume);
    const peakYear = years[maxIndex];
    const troughYear = years[minIndex];

    // Calculate recent YoY growth (last two years)
    let yoyGrowth = 0;
    if (volumes.length >= 2) {
      const currentYear = volumes[volumes.length - 1];
      const previousYear = volumes[volumes.length - 2];
      yoyGrowth = ((currentYear - previousYear) / previousYear * 100);
    }

    // Calculate decline from peak (if applicable)
    const currentVolume = volumes[volumes.length - 1];
    const declineFromPeak = ((currentVolume - maxVolume) / maxVolume * 100);

    // Determine market phase and create comprehensive stat
    let statText = '';
    let statColor = '#9E9E9E';

    if (Math.abs(declineFromPeak) < 5) {
      // Near peak
      statText = `📊 Peak: ${maxVolume.toLocaleString()} (${peakYear}) • ${yoyGrowth > 0 ? '↗' : '↘'} ${Math.abs(yoyGrowth).toFixed(1)}% YoY`;
      statColor = yoyGrowth > 0 ? '#4CAF50' : '#FFA726';
    } else if (declineFromPeak < -10) {
      // Significant decline from peak
      statText = `📉 Down ${Math.abs(declineFromPeak).toFixed(1)}% from peak ${maxVolume.toLocaleString()} (${peakYear}) • ${yoyGrowth.toFixed(1)}% YoY`;
      statColor = '#F44336';
    } else if (yoyGrowth > 5) {
      // Strong recent growth
      statText = `📈 ${yoyGrowth.toFixed(1)}% YoY • Peak: ${maxVolume.toLocaleString()} (${peakYear})`;
      statColor = '#4CAF50';
    } else {
      // Standard display
      const trendIcon = yoyGrowth > 0 ? '↗' : '↘';
      statText = `${trendIcon} ${Math.abs(yoyGrowth).toFixed(1)}% YoY • Peak: ${maxVolume.toLocaleString()} (${peakYear})`;
      statColor = yoyGrowth > 0 ? '#4CAF50' : (yoyGrowth < -5 ? '#F44336' : '#FFA726');
    }

    // Update stat display with comprehensive information
    const statElement = document.getElementById('volume-chart-stat');
    statElement.innerHTML = `<span style="color:${statColor}; font-weight:800;">${statText}</span>`;
    statElement.style.display = 'block';

    // Destroy existing chart instance if it exists
    if (volumeChartInstance) {
      volumeChartInstance.destroy();
    }

    const canvas = document.getElementById('volumeChart');
    if (!canvas) {
      console.error('Volume canvas element not found!');
      return;
    }

    const ctx = canvas.getContext('2d');

    volumeChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: years,
        datasets: [{
          label: 'Transaction Volume',
          data: volumes,
          backgroundColor: 'rgba(99, 102, 241, 0.9)', // Solid, crisp Royal Indigo
          borderColor: 'transparent',
          borderWidth: 0,
          borderRadius: { topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0 }, // Sharp sleek corners
          hoverBackgroundColor: 'rgba(79, 70, 229, 1)', // Hover Dark Indigo
          barThickness: 'flex',
          maxBarThickness: 32,
          barPercentage: 0.75, // Thicker, sharper bars
          categoryPercentage: 0.85
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        animation: {
          duration: 800,
          easing: 'easeOutQuart',
          delay: (context) => {
            if (context.type !== 'data') return 0;
            return context.dataIndex * 120;
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(15, 23, 42, 0.9)', // Match Nocturnal Theme
            borderColor: 'rgba(99, 102, 241, 0.4)', // Indigo
            borderWidth: 1,
            titleColor: '#818CF8', // Light Indigo
            bodyColor: '#e2e2e8',
            titleFont: {
              family: 'Outfit',
              weight: '700',
              size: 12
            },
            bodyFont: {
              family: 'Inter',
              size: 11,
              weight: '500'
            },
            padding: 12,
            cornerRadius: 8,
            caretSize: 6,
            displayColors: false,
            callbacks: {
              title: (context) => {
                return `Year ${context[0].label}`;
              },
              label: (context) => {
                const volume = context.parsed.y;
                const index = context.dataIndex;

                // Calculate YoY change if not first point
                let changeText = '';
                if (index > 0) {
                  const prevVolume = volumes[index - 1];
                  const change = ((volume - prevVolume) / prevVolume * 100).toFixed(1);
                  const changeIcon = change > 0 ? '↑' : '↓';
                  changeText = ` (${changeIcon}${Math.abs(change)}% YoY)`;
                }

                return `${volume.toLocaleString()} transactions${changeText}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: true,
              color: 'rgba(59, 130, 246, 0.05)',
              lineWidth: 1
            },
            ticks: {
              color: '#9E9E9E',
              font: {
                family: 'Outfit',
                size: 9,
                weight: '600'
              },
              padding: 4
            },
            border: {
              color: 'rgba(59, 130, 246, 0.2)'
            }
          },
          y: {
            grid: {
              color: 'rgba(99, 102, 241, 0.08)',
              lineWidth: 1
            },
            ticks: {
              color: '#9E9E9E',
              font: {
                family: 'Outfit',
                size: 9,
                weight: '600'
              },
              padding: 4,
              callback: (v) => {
                if (v >= 1000) {
                  return (v / 1000).toFixed(1) + 'k';
                }
                return v;
              }
            },
            border: {
              color: 'rgba(99, 102, 241, 0.2)'
            }
          }
        }
      }
    });

    console.log('Volume chart created successfully:', volumeChartInstance);
  }

  // FETCH PROPERTY COSTS DYNAMICALLY
  function fetchPropertyCosts(locationName) {
    const container = document.getElementById('property-costs-container');

    // Reset global data
    currentCostData = null;

    // Show loading state
    container.innerHTML = `
      <div style="text-align:center; padding:20px; color:#666;">
        <div style="font-size:12px;">Loading property costs...</div>
      </div>
    `;

    callSupabaseRPC('get_property_costs_func', { area_name: locationName })
      .then(data => {
        // Handle the different response format from Supabase RPC
        const result = Array.isArray(data) && data.length > 0 ? data[0] : data;
        if (!result || result.error) {
          currentCostData = null;
          // No data available
          container.innerHTML = `
            <div style="text-align:center; padding:20px; color:#666;">
              <div style="font-size:11px;">Property cost data not available for this location</div>
            </div>
          `;
          return;
        }

        // Store for PDF Report
        currentCostData = {
          location: result.location,
          count: result.count,
          avgBase: result.avgbase,
          avgSqft: result.avgsqft,
          minBase: result.minbase || result.avgbase,
          maxBase: result.maxbase || result.avgbase,
          minSqft: result.minsqft,
          maxSqft: result.maxsqft
        };

        // NEW: Update the Investment Fact Placeholder text immediately
        const invFactSpan = document.getElementById("invest-fact-price");
        if (invFactSpan) {
          invFactSpan.innerText = ` (~₹${result.avgsqft.toLocaleString()}/sqft)`;
          invFactSpan.style.opacity = 1;
        }

        // Calculate unique project count from the properties data
        let projectCount = result.count; // fallback to total property count
        if (result.properties && Array.isArray(result.properties)) {
          const uniqueProjects = new Set(result.properties.map(p => p.project_name || p.project_id));
          projectCount = uniqueProjects.size;
        } else if (window.currentProjectsList && window.currentProjectsList.length > 0) {
          projectCount = window.currentProjectsList.length;
        }

        // Render the property costs section
        container.innerHTML = `
          <div style="margin: 12px 12px 0; padding-top:12px; border-top:1px solid var(--border);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <span style="font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:2.5px; color:var(--gold); font-family:'Outfit',sans-serif;">💰 Property Costs</span>
              <span style="font-size:9px; color:var(--t3); background:rgba(255,255,255,0.05); padding:4px 10px; border-radius:8px; border:1px solid var(--border-subtle); font-family:'Outfit',sans-serif; font-weight:600;">${projectCount} Props</span>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-bottom:7px;">
              <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:12px; border:1px solid var(--border-subtle); border-top:2px solid var(--gold); box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size:8px; color:var(--t3); margin-bottom:6px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Avg Base</div>
                <div style="font-size:1.25rem; font-weight:800; color:var(--gold-light); font-family:'Outfit',sans-serif; letter-spacing:-0.3px;">₹${result.avgbase} Cr</div>
              </div>
              <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:12px; border:1px solid var(--border-subtle); border-top:2px solid var(--teal); box-shadow:0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size:8px; color:var(--t3); margin-bottom:6px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Avg / SqFt</div>
                <div style="font-size:1.25rem; font-weight:800; color:var(--teal); font-family:'Outfit',sans-serif; letter-spacing:-0.3px;">₹${result.avgsqft.toLocaleString()}</div>
              </div>
            </div>
            
            <div style="padding:12px 14px; background:rgba(255,255,255,0.02); border:1px solid var(--border-subtle); border-radius:12px; margin-bottom:8px; box-shadow:0 4px 12px rgba(0,0,0,0.15);">
              <div style="font-size:8px; color:var(--t3); margin-bottom:8px; text-transform:uppercase; font-weight:700; letter-spacing:1.5px; font-family:'Outfit',sans-serif;">Base Price Range</div>
              <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">₹${result.minbase || result.avgbase} Cr</span>
                <div style="flex:1; height:4px; background:rgba(255,255,255,0.08); border-radius:4px; position:relative;">
                  <div style="position:absolute; inset:0; background:linear-gradient(90deg, var(--gold), var(--gold-light)); border-radius:4px;"></div>
                </div>
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">₹${result.maxbase || result.avgbase} Cr</span>
              </div>
            </div>
            <div style="padding:10px 12px; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; box-shadow:0 1px 4px rgba(26,26,46,0.04);">
              <div style="font-size:8px; color:var(--t4); margin-bottom:6px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Price / SqFt Range</div>
              <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">&#8377;${result.minsqft.toLocaleString()}</span>
                <div style="flex:1; height:3px; background:var(--border); border-radius:2px; position:relative;">
                  <div style="position:absolute; inset:0; background:linear-gradient(90deg, var(--teal), #0A8A8E); border-radius:2px;"></div>
                </div>
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">&#8377;${result.maxsqft.toLocaleString()}</span>
              </div>
            </div>
          </div>
        `;
      })
      .catch(err => {
        console.error("Property Costs Fetch Error:", err);
        container.innerHTML = `
          <div style="text-align:center; padding:20px; color:#f87171;">
            <div style="font-size:11px;">Failed to load property costs</div>
          </div>
        `;
      });
  }

  // FETCH FUTURE DEVELOPMENT DATA DYNAMICALLY
  function fetchFutureDevelopment(locationId) {
    console.log('fetchFutureDevelopment called with locationId:', locationId);
    const container = document.getElementById('future-dev-container');

    if (!container) {
      console.error('future-dev-container element not found!');
      return;
    }

    // Show loading state
    container.innerHTML = `
      <div style="text-align:center; padding:20px; color:#666;">
        <div style="font-size:12px;">Loading future developments...</div>
      </div>
    `;

    // Use the configured API URL from config.js
    const PYTHON_API_URL = window.API_BASE_URL;

    const futureDevUrl = `${PYTHON_API_URL}/api/v1/future-development/${locationId}`;
    console.log('🔍 Fetching future development from:', futureDevUrl);

    fetch(futureDevUrl)
      .then(response => {
        console.log('Future Dev API Response Status:', response.status);
        return response.json();
      })
      .then(data => {
        console.log('Future Dev API Data:', data);
        if (!data.success || !data.developments || data.developments.length === 0) {
          container.innerHTML = `
            <div style="text-align:center; padding:20px; color:#666;">
              <div style="font-size:11px;">No future development data available for this location</div>
            </div>
          `;
          return;
        }

        // Render future development items
        const developmentsHtml = data.developments.map(dev => {
          const publishedDate = dev.published_at ? new Date(dev.published_at).toLocaleDateString() : 'Date unknown';
          const yearMentioned = dev.year_mentioned ? ` (${dev.year_mentioned})` : '';

          return `
            <div class="future-dev-item" style="margin-bottom:12px; padding:14px; background:rgba(255,255,255,0.03); border:1px solid var(--border-subtle); border-radius:12px; border-left:3px solid var(--blue); box-shadow:0 2px 8px rgba(0,0,0,0.1);">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:1px; font-family:'Outfit',sans-serif;">
                  ${dev.source}${yearMentioned}
                </div>
                <div style="font-size:9px; color:var(--t3); font-family:'Outfit',sans-serif;">
                  ${publishedDate}
                </div>
              </div>
              <div style="font-size:12px; line-height:1.5; color:var(--t2); font-family:'Inter',sans-serif;">
                ${dev.content}
              </div>
              ${dev.content.length >= 200 ? `
                <button class="expand-dev-btn" onclick="window.expandDevelopment(${dev.id})" style="margin-top:8px; font-size:10px; color:var(--blue); background:none; border:none; cursor:pointer; text-decoration:underline; font-family:'Outfit',sans-serif;">
                  Read more...
                </button>
              ` : ''}
            </div>
          `;
        }).join('');

        container.innerHTML = `
          <div style="margin: 12px 12px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <span style="font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:2.5px; color:var(--blue); font-family:'Outfit',sans-serif;">🏗️ Future Projects</span>
              <span style="font-size:9px; color:var(--t3); background:rgba(255,255,255,0.05); padding:4px 10px; border-radius:8px; border:1px solid var(--border-subtle); font-family:'Outfit',sans-serif; font-weight:600;">${data.total_count} Items</span>
            </div>
            ${developmentsHtml}
          </div>
        `;

        // Store development data globally for potential use in reports
        window.currentFutureDevelopments = data.developments;
      })
      .catch(err => {
        console.error("Future Development Fetch Error:", err);
        container.innerHTML = `
          <div style="text-align:center; padding:20px; color:#f87171;">
            <div style="font-size:11px;">Failed to load future development data</div>
            <div style="font-size:10px; margin-top:4px; color:#666;">Check console for details</div>
          </div>
        `;
      });
  }





  // OPEN FUTURE DEVELOPMENT MODAL (called from popup click)
  function openFutureDevelopmentModal(locationName, locationId) {
    console.log('🚀 openFutureDevelopmentModal called for:', locationName);

    // Close the small popup
    if (futureDevPopup) futureDevPopup.remove();

    // Create modal if it doesn't exist
    let modal = document.getElementById('future-dev-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'future-dev-modal';
      modal.className = 'future-dev-modal';
      document.body.appendChild(modal);
    }

    // Show modal with loading state
    modal.innerHTML = `
      <div class="modal-overlay" onclick="closeFutureDevelopmentModal()">
        <div class="modal-content" onclick="event.stopPropagation()">
          <div class="modal-header">
            <h2>🏗️ Future Development - ${locationName}</h2>
            <button class="modal-close" onclick="closeFutureDevelopmentModal()">×</button>
          </div>
          <div class="modal-body">
            <div class="loading-state">
              <div class="loading-spinner"></div>
              <p>Loading future developments...</p>
            </div>
          </div>
        </div>
      </div>
    `;

    modal.style.display = 'flex';

    // Fetch and display future development data
    fetchFutureDevelopmentForModal(locationId, locationName);
  }

  // Make openFutureDevelopmentModal globally accessible
  window.openFutureDevelopmentModal = openFutureDevelopmentModal;

  // CLOSE FUTURE DEVELOPMENT MODAL
  function closeFutureDevelopmentModal() {
    const modal = document.getElementById('future-dev-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  }

  // Make close function globally accessible
  window.closeFutureDevelopmentModal = closeFutureDevelopmentModal;

  // FETCH FUTURE DEVELOPMENT DATA FOR MODAL
  function fetchFutureDevelopmentForModal(locationId, locationName) {
    // Use the configured API URL from config.js
    const PYTHON_API_URL = window.API_BASE_URL;

    const futureDevUrl = `${PYTHON_API_URL}/api/v1/future-development/${locationId}`;
    console.log('🔍 Fetching future development for modal:', futureDevUrl);

    fetch(futureDevUrl)
      .then(response => response.json())
      .then(data => {
        const modal = document.getElementById('future-dev-modal');
        if (!modal) return; // Modal was closed

        const modalBody = modal.querySelector('.modal-body');

        if (!data.success || !data.developments || data.developments.length === 0) {
          modalBody.innerHTML = `
            <div class="no-data-state">
              <div class="no-data-icon">📋</div>
              <h3>No Future Development Data</h3>
              <p>No upcoming projects or infrastructure developments found for ${locationName}.</p>
            </div>
          `;
          return;
        }

        // Render future development items for modal
        const developmentsHtml = data.developments.map(dev => {
          const publishedDate = dev.published_at ? new Date(dev.published_at).toLocaleDateString() : 'Date unknown';
          const yearMentioned = dev.year_mentioned ? ` (${dev.year_mentioned})` : '';

          return `
            <div class="dev-item">
              <div class="dev-header">
                <div class="dev-source">${dev.source}${yearMentioned}</div>
                <div class="dev-date">${publishedDate}</div>
              </div>
              <div class="dev-content">
                ${dev.content}
              </div>
            </div>
          `;
        }).join('');

        modalBody.innerHTML = `
          <div class="dev-summary">
            <div class="dev-count">${data.total_count} Future Development Projects</div>
            <div class="dev-subtitle">Upcoming projects & infrastructure developments</div>
          </div>
          <div class="dev-list">
            ${developmentsHtml}
          </div>
        `;
      })
      .catch(err => {
        console.error("Future Development Modal Fetch Error:", err);
        const modal = document.getElementById('future-dev-modal');
        if (modal) {
          const modalBody = modal.querySelector('.modal-body');
          modalBody.innerHTML = `
            <div class="error-state">
              <div class="error-icon">⚠️</div>
              <h3>Failed to Load Data</h3>
              <p>Unable to fetch future development information for ${locationName}.</p>
              <button onclick="fetchFutureDevelopmentForModal(${locationId}, '${locationName}')" class="retry-btn">
                Try Again
              </button>
            </div>
          `;
        }
      });
  }

  // Make expandDevelopment globally accessible
  window.expandDevelopment = function (devId) {
    const developments = window.currentFutureDevelopments || [];
    const dev = developments.find(d => d.id === devId);

    if (!dev) return;

    // Create modal or expand inline
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
      background: rgba(0,0,0,0.8); z-index: 10000; 
      display: flex; align-items: center; justify-content: center;
      padding: 20px;
    `;

    modal.innerHTML = `
      <div style="background: var(--bg-card); border-radius: 16px; padding: 24px; max-width: 600px; max-height: 80vh; overflow-y: auto; border: 1px solid var(--border);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="color: var(--blue); font-family: 'Outfit', sans-serif; margin: 0;">${dev.source}</h3>
          <button onclick="this.closest('.modal').remove()" style="background: none; border: none; font-size: 20px; color: var(--t3); cursor: pointer;">×</button>
        </div>
        <div style="font-size: 14px; line-height: 1.6; color: var(--t2); font-family: 'Inter', sans-serif;">
          ${dev.full_content}
        </div>
      </div>
    `;

    modal.className = 'modal';
    document.body.appendChild(modal);

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });
  };

  // ===============================
  // AMENITY DISPLAY FUNCTIONS
  // ===============================
  // Amenities state is now global (see top of file)

  function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.getElementById('notification-toast');
    if (existing) existing.remove();

    // Create notification
    const notification = document.createElement('div');
    notification.id = 'notification-toast';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 16px;
      border-radius: 8px;
      color: white;
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      z-index: 10000;
      max-width: 300px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      transition: all 0.3s ease;
    `;

    // Set color based on type
    const colors = {
      info: '#3b82f6',
      warning: '#f59e0b',
      error: '#ef4444',
      success: '#10b981'
    };
    notification.style.backgroundColor = colors[type] || colors.info;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Auto remove after 3 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
      }
    }, 3000);
  }

  function displayAmenitiesOnMap(locationId, amenityType) {
    console.log(`🚀 displayAmenitiesOnMap called — locationId=${locationId} type=${amenityType}`);
    // Remove existing amenity layers
    clearAmenities();

    // Show loading state
    const buttons = document.querySelectorAll('.amenity-btn');
    buttons.forEach(btn => {
      if (btn.dataset.amenity === amenityType) {
        btn.innerHTML = `⏳ Loading...`;
        btn.disabled = true;
      }
    });

    // Get location coordinates from the insights data
    const locationData = Array.isArray(window.insightsData)
      ? window.insightsData.find(d => d.location_id === locationId)
      : null;

    if (!locationData) {
      console.log('ℹ️ Please select a location first');
      resetAmenityButtons(amenityType);
      return;
    }

    const lat = parseFloat(locationData.latitude);
    const lng = parseFloat(locationData.longitude);

    // Lenient coordinate validation - just check if they exist and are numbers
    if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
      console.log('ℹ️ Location coordinates not available');
      resetAmenityButtons(amenityType);
      return;
    }

    console.log('✅ Valid coordinates found:', { lat, lng, locationId });

    // ─── Column name map (amenityType → DB column) ───────────────────────────
    const dbColumnMap = {
      hospitals: 'hospitals_data', schools: 'schools_data', malls: 'malls_data',
      restaurants: 'restaurants_data', banks: 'banks_data', parks: 'parks_data', metro: 'metro_data'
    };
    const dbCountMap = {
      hospitals: 'hospital_count', schools: 'school_count', malls: 'malls_count',
      restaurants: 'restaurants_count', banks: 'banks_count', parks: 'parks_count', metro: 'metro_count'
    };
    const dataCol = dbColumnMap[amenityType];
    const countCol = dbCountMap[amenityType];

    // ─── Helper: read cached amenity data from Supabase locations table ──────
    async function fetchFromDB() {
      if (!locationId || !dataCol) {
        console.log(`⚠️ fetchFromDB skip — locationId=${locationId} dataCol=${dataCol}`);
        return null;
      }
      const url = `${SUPABASE_URL}/rest/v1/locations?id=eq.${locationId}&select=${dataCol}`;
      console.log(`🗄️ fetchFromDB GET:`, url);
      const res = await fetch(url, {
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` }
      });
      if (!res.ok) { console.error(`❌ fetchFromDB GET failed (${res.status})`); return null; }
      const rows = await res.json();
      console.log(`🗄️ fetchFromDB rows:`, rows);
      const val = rows?.[0]?.[dataCol];
      return Array.isArray(val) && val.length > 0 ? val : null;
    }

    // ─── Helper: persist fetched amenities back to DB ────────────────────────
    async function saveToDB(amenities) {
      if (!locationId || !dataCol) {
        console.error(`❌ saveToDB skip — locationId=${locationId} dataCol=${dataCol}`);
        return;
      }
      const body = { [dataCol]: amenities, [countCol]: amenities.length };
      console.log(`💾 saveToDB PATCH → location=${locationId} col=${dataCol} count=${amenities.length}`);
      const res = await fetch(`${SUPABASE_URL}/rest/v1/locations?id=eq.${locationId}`, {
        method: 'PATCH',
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal'
        },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const errText = await res.text();
        console.error(`❌ saveToDB PATCH failed (${res.status}):`, errText);
        showDbStatus(`❌ Save failed (${res.status}): ${errText}`, 'red');
      } else {
        console.log(`✅ saveToDB success — ${amenities.length} ${amenityType} saved for location ${locationId}`);
        showDbStatus(`✅ Saved ${amenities.length} ${amenityType} to DB (loc ${locationId})`, 'green');
      }

      function showDbStatus(msg, color) {
        const el = document.createElement('div');
        el.style.cssText = `position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:${color === 'green' ? '#166534' : '#7f1d1d'};color:#fff;padding:8px 16px;border-radius:8px;font-size:13px;z-index:99999;max-width:90vw;word-break:break-all`;
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 6000);
      }
    }

    // ─── Overpass fetch (parallel mirror race + in-memory cache) ─────────────
    const overpassTagMap = {
      hospitals: '[amenity=hospital]',
      schools: '[amenity=school]',
      malls: '[shop=mall]',
      restaurants: '[amenity=restaurant]',
      banks: '[amenity=bank]',
      parks: '[leisure=park]',
      metro: '[railway=station]'
    };
    const colorMap = {
      hospitals: '#ef4444', schools: '#3b82f6', malls: '#a855f7',
      restaurants: '#f97316', banks: '#22c55e', parks: '#14b8a6', metro: '#eab308'
    };
    const tag = overpassTagMap[amenityType] || `[amenity=${amenityType}]`;
    const radius = 4000; // 4 km radius
    const overpassQuery = `[out:json][timeout:10][maxsize:500000];(node${tag}(around:${radius},${lat},${lng});way${tag}(around:${radius},${lat},${lng}););out center 8;`;
    const encodedQuery = encodeURIComponent(overpassQuery);

    // Cache keyed by location+type — instant on repeat clicks
    if (!window._amenityCache) window._amenityCache = {};
    const cacheKey = `${lat.toFixed(4)},${lng.toFixed(4)},${amenityType}`;
    if (window._amenityCache[cacheKey]) {
      console.log(`⚡ Cache hit for ${amenityType}`);
    }

    // Haversine distance in km
    function haversine(lat1, lng1, lat2, lng2) {
      const R = 6371, dLat = (lat2 - lat1) * Math.PI / 180, dLng = (lng2 - lng1) * Math.PI / 180;
      const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
      return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    // Fetch from one mirror with a per-mirror timeout
    function fetchMirror(url, timeoutMs) {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('timeout')), timeoutMs);
        fetch(url)
          .then(res => {
            clearTimeout(timer);
            if (!res.ok) throw new Error(`${res.status}`);
            return res.text();
          })
          .then(text => {
            if (text.startsWith('<')) throw new Error('HTML error');
            resolve(JSON.parse(text));
          })
          .catch(err => { clearTimeout(timer); reject(err); });
      });
    }

    // Race all mirrors in parallel — return the first to succeed
    function fetchRace(encodedQ) {
      const mirrors = [
        `https://overpass.kumi.systems/api/interpreter?data=${encodedQ}`,
        `https://overpass-api.de/api/interpreter?data=${encodedQ}`,
        `https://overpass.openstreetmap.ru/api/interpreter?data=${encodedQ}`
      ];
      let resolved = false;
      return new Promise((resolve, reject) => {
        let failures = 0;
        mirrors.forEach(url => {
          fetchMirror(url, 8000).then(data => {
            if (!resolved) { resolved = true; resolve(data); }
          }).catch(() => {
            failures++;
            if (failures === mirrors.length) reject(new Error('All mirrors failed'));
          });
        });
      });
    }

    // ─── Main flow: DB → in-memory cache → Overpass API ─────────────────────
    async function resolveAmenities() {
      // 1. In-memory cache (instant, same session)
      if (window._amenityCache[cacheKey]) {
        console.log(`⚡ In-memory cache hit for ${amenityType}`);
        return { amenities: window._amenityCache[cacheKey], fromCache: true };
      }

      // 2. Supabase DB cache (persisted, first hit per location)
      console.log(`🗄️ Checking DB cache for ${amenityType} at location ${locationId}…`);
      const dbAmenities = await fetchFromDB();
      if (dbAmenities) {
        console.log(`✅ DB cache hit — ${dbAmenities.length} ${amenityType} loaded from DB`);
        window._amenityCache[cacheKey] = dbAmenities; // promote to in-memory
        return { amenities: dbAmenities, fromCache: true };
      }

      // 3. Overpass API (first ever fetch for this location+type)
      console.log(`🌐 No cache — fetching ${amenityType} from Overpass API…`);
      const osm = await fetchRace(encodedQuery);
      const amenities = (osm.elements || [])
        .map(el => {
          const elLat = el.lat ?? el.center?.lat;
          const elLng = el.lon ?? el.center?.lon;
          if (!elLat || !elLng) return null;
          return {
            name: el.tags?.name || el.tags?.amenity || amenityType,
            latitude: elLat,
            longitude: elLng,
            distance_km: parseFloat(haversine(lat, lng, elLat, elLng).toFixed(2)),
            address: el.tags?.['addr:street'] || '',
            rating: null,
            color: colorMap[amenityType] || '#6366f1'
          };
        })
        .filter(Boolean)
        .sort((a, b) => a.distance_km - b.distance_km)
        .slice(0, 8);

      // Save to DB and in-memory cache for future hits
      window._amenityCache[cacheKey] = amenities;
      saveToDB(amenities); // fire-and-forget
      return { amenities, fromCache: false };
    }

    resolveAmenities()
      .then(({ amenities, fromCache }) => {
        const data = { amenities };

        if (!data.amenities || data.amenities.length === 0) {
          console.log('ℹ️ No amenities found in this area');
          resetAmenityButtons(amenityType);
          return;
        }

        console.log(`✅ ${fromCache ? '(cached)' : '(live)'} ${data.amenities.length} ${amenityType}`);

        // Show amenities panel on the right side
        showAmenitiesPanel(data.amenities, amenityType);

        // Hide layers card if open
        const layersCard = document.getElementById("layers-card");
        if (layersCard) layersCard.style.display = 'none';

        // Store for PDF Report
        currentAmenityList = data.amenities.map(a => ({ name: a.name, dist: a.distance_km }));
        currentAmenityType = amenityType.charAt(0).toUpperCase() + amenityType.slice(1);

        // Create GeoJSON from amenities
        const geojson = {
          type: 'FeatureCollection',
          features: data.amenities.map(amenity => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [amenity.longitude, amenity.latitude]
            },
            properties: {
              name: amenity.name,
              distance: amenity.distance_km,
              color: amenity.color
            }
          }))
        };

        // Add source WITHOUT clustering - show all amenities individually
        map.addSource('amenity-data', {
          type: 'geojson',
          data: geojson,
          cluster: false  // Disable clustering to show all amenities at any zoom level
        });

        // Add individual amenity markers without clustering
        const customIconId = `icon-${amenityType}`;

        map.addLayer({
          id: 'amenity-markers',
          type: 'symbol',
          source: 'amenity-data',
          layout: {
            'icon-image': customIconId,
            'icon-size': 0.05,  // Reduced size for custom PNG icons
            'icon-anchor': 'bottom',
            'icon-allow-overlap': true,
            'icon-ignore-placement': false
          },
          minzoom: 0,  // Visible at all zoom levels
          maxzoom: 24  // Visible at all zoom levels
        });

        currentAmenityLayer = 'amenity-markers';




        // Add click handler for amenity markers
        map.on('click', 'amenity-markers', (e) => {
          const coordinates = e.features[0].geometry.coordinates.slice();
          const { name, distance, color } = e.features[0].properties;

          const colorLabel = color === 'green' ? '0-2km' : color === 'orange' ? '2-3.5km' : '3.5-5km';
          const colorHex = color === 'green' ? '#4ade80' : color === 'orange' ? '#fb923c' : '#ef4444';

          if (currentPopup) currentPopup.remove();

          currentPopup = new maplibregl.Popup({ closeButton: true, closeOnClick: true, maxWidth: '240px' })
            .setLngLat(coordinates)
            .setHTML(`
              <div class="popup-container" style="padding:16px;">
                <div class="popup-title serif" style="font-size:16px; margin-bottom:8px;">${name}</div>
                <div style="display:flex; gap:6px; flex-wrap:wrap;">
                  <span style="background:#E6F4EA; color:#166534; padding:4px 8px; border-radius:12px; font-size:10px; font-weight:600; border:1px solid #16653430;">📍 ${distance} km</span>
                  <span style="background:#F1F5F9; color:#334155; padding:4px 8px; border-radius:12px; font-size:10px; font-weight:600; text-transform:uppercase; border:1px solid #33415530;">${colorLabel}</span>
                </div>
              </div>
            `)
            .addTo(map);
        });

        // Change cursor on hover
        map.on('mouseenter', 'amenity-markers', () => {
          map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', 'amenity-markers', () => {
          map.getCanvas().style.cursor = '';
        });

        // Update button to show count
        resetAmenityButtons(amenityType, data.total_count);

        // Fit map to show all amenities
        const bounds = new maplibregl.LngLatBounds();
        data.amenities.forEach(amenity => {
          bounds.extend([amenity.longitude, amenity.latitude]);
        });
        bounds.extend([data.location_lng, data.location_lat]);
        map.fitBounds(bounds, { padding: 50, maxZoom: 13 });

        // Store for PDF report
        currentAmenityList = data.amenities;
        currentAmenityType = amenityType.charAt(0).toUpperCase() + amenityType.slice(1);

        // Show the clear button
        const clearBtn = document.getElementById('clear-amenities-btn');
        if (clearBtn) clearBtn.style.display = 'block';

        /* ===============================
           POPULATE AMENITY LIST CARD
        =============================== */
        const listCard = document.getElementById('amenities-list-card');
        const listContent = document.getElementById('amenities-list-content');
        const listTitle = document.getElementById('amenity-title');

        console.log('🔍 Amenity list elements:', { listCard: !!listCard, listContent: !!listContent, listTitle: !!listTitle });

        if (listCard && listContent && listTitle) {
          // Update Title - Simple text only
          const typeName = amenityType.charAt(0).toUpperCase() + amenityType.slice(1);
          listTitle.textContent = `${typeName} nearby`;

          // Clear previous list
          listContent.innerHTML = '';

          // Sort by distance (just in case)
          const sortedAmenities = data.amenities.sort((a, b) => a.distance_km - b.distance_km);

          sortedAmenities.forEach(amenity => {
            const item = document.createElement('div');
            item.className = 'amenity-item';

            // Color tag based on distance
            let colorHex = '#ef4444'; // red
            let colorLabel = '3.5-5km';
            if (amenity.color === 'green') { colorHex = '#4ade80'; colorLabel = '0-2km'; }
            if (amenity.color === 'orange') { colorHex = '#fb923c'; colorLabel = '2-3.5km'; }

            item.innerHTML = `
              <div class="amenity-info">
                <div class="amenity-name">${amenity.name}</div>
                <div class="amenity-badges">
                  <span class="amenity-badge amenity-badge-distance">${amenity.distance_km} km</span>
                  <span class="amenity-badge amenity-badge-range">${colorLabel}</span>
                </div>
              </div>
            `;

            // Click to Fly - Enhanced with debugging and better event handling
            item.style.cursor = 'pointer';
            item.addEventListener('click', function (e) {
              e.preventDefault();
              e.stopPropagation();

              console.log('🔍 Amenity clicked:', amenity.name);
              console.log('🔍 Coordinates:', amenity.longitude, amenity.latitude);

              if (!amenity.longitude || !amenity.latitude) {
                console.error('❌ Missing coordinates for:', amenity.name);
                return;
              }

              console.log('🚀 Flying to amenity location...');

              // Use the navigateToAmenity function which is proven to work
              navigateToAmenity(amenity.longitude, amenity.latitude, amenity.name);

              console.log('✅ Navigation should be complete');
            });

            listContent.appendChild(item);
          });

          // Show Card
          listCard.style.display = 'flex';
          console.log('✅ Amenities list card should now be visible');
        } else {
          console.error('❌ Amenities list elements not found:', {
            listCard: !!listCard,
            listContent: !!listContent,
            listTitle: !!listTitle
          });
        }

      })
      .catch(err => {
        console.log('ℹ️ Amenities temporarily unavailable for this location');
        resetAmenityButtons(amenityType);
      });
  }

  function clearAmenities() {
    // Show properties panel again when amenities are cleared
    const propertiesPanel = document.getElementById('properties-panel');
    if (propertiesPanel) {
      propertiesPanel.style.display = 'flex';
    }

    // Hide amenities panel
    const amenitiesPanel = document.getElementById('amenities-panel');
    if (amenitiesPanel) {
      amenitiesPanel.style.display = 'none';
    }

    // Hide the clear button
    const clearBtn = document.getElementById('clear-amenities-btn');
    if (clearBtn) clearBtn.style.display = 'none';

    // Hide the list card
    const listCard = document.getElementById('amenities-list-card');
    if (listCard) listCard.style.display = 'none';

    // Remove any open popup
    if (currentPopup) {
      currentPopup.remove();
      currentPopup = null;
    }

    if (currentAmenityLayer) {
      if (map.getLayer('amenity-clusters')) map.removeLayer('amenity-clusters');
      if (map.getLayer('amenity-cluster-counts')) map.removeLayer('amenity-cluster-counts');
      if (map.getLayer('amenity-markers')) map.removeLayer('amenity-markers');
      if (map.getSource('amenity-data')) map.removeSource('amenity-data');
      currentAmenityLayer = null;

      // Reset buttons
      const buttons = document.querySelectorAll('.amenity-btn');
      buttons.forEach(btn => {
        btn.style.opacity = '0.7';
        btn.style.transform = 'scale(1)';
        btn.disabled = false;
        const type = btn.dataset.amenity;
        const icons = { hospitals: '🏥', schools: '🏫', malls: '🏪', restaurants: '🍽️', banks: '🏦', parks: '🏞️', metro: '🚇' };
        const labels = { hospitals: 'Hospitals', schools: 'Schools', malls: 'Malls', restaurants: 'Food', banks: 'Banks', parks: 'Parks', metro: 'Metro' };
        btn.innerHTML = `<span class="btn-icon">${icons[type] || '📍'}</span><span class="btn-label">${labels[type] || type}</span>`;
      });
    }
  }

  // Make clearAmenities globally accessible
  // Helper functions for the amenities panel
  function getAmenityConfig(amenityType) {
    const configs = {
      hospitals: {
        icon: '🏥',
        label: 'Healthcare Centers',
        gradient: 'linear-gradient(135deg, #ff6b6b, #ee5a52)'
      },
      schools: {
        icon: '🎓',
        label: 'Educational Institutions',
        gradient: 'linear-gradient(135deg, #4ecdc4, #44a08d)'
      },
      parks: {
        icon: '🌳',
        label: 'Parks & Recreation',
        gradient: 'linear-gradient(135deg, #a8e6cf, #7fcdcd)'
      },
      malls: {
        icon: '🛍️',
        label: 'Shopping Centers',
        gradient: 'linear-gradient(135deg, #ffd93d, #ff6b6b)'
      },
      restaurants: {
        icon: '🍽️',
        label: 'Restaurants & Dining',
        gradient: 'linear-gradient(135deg, #ff9a9e, #fecfef)'
      },
      banks: {
        icon: '🏦',
        label: 'Banks & ATMs',
        gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
      },
      metro: {
        icon: '🚇',
        label: 'Metro Stations',
        gradient: 'linear-gradient(135deg, #f093fb, #f5576c)'
      }
    };
    return configs[amenityType] || {
      icon: '📍',
      label: 'Amenities',
      gradient: 'linear-gradient(135deg, #a8edea, #fed6e3)'
    };
  }

  function calculateAverageDistance(amenities) {
    if (!amenities.length) return 'N/A';
    const total = amenities.reduce((sum, amenity) => sum + parseFloat(amenity.distance_km), 0);
    return (total / amenities.length).toFixed(1) + ' km';
  }

  function navigateToAmenity(longitude, latitude, name) {
    console.log(`🧭 Navigating to: ${name} at [${longitude}, ${latitude}]`);

    // Fly to the amenity location
    map.flyTo({
      center: [longitude, latitude],
      zoom: 17,
      duration: 1500,
      essential: true
    });

    // Show notification
    showNotification(`📍 Navigating to ${name}`, 'success');

    // Optional: Add a temporary marker
    setTimeout(() => {
      const popup = new maplibregl.Popup({ closeOnClick: true })
        .setLngLat([longitude, latitude])
        .setHTML(`
          <div style="text-align: center; padding: 8px;">
            <strong>${name}</strong><br>
            <small style="color: #666;">You have arrived!</small>
          </div>
        `)
        .addTo(map);

      // Auto-close popup after 3 seconds
      setTimeout(() => popup.remove(), 3000);
    }, 1500);
  }

  // Make navigateToAmenity globally accessible
  window.navigateToAmenity = navigateToAmenity;

  window.clearAmenities = clearAmenities;

  function showAmenitiesPanel(amenities, amenityType) {
    // Hide properties panel
    const propertiesPanel = document.getElementById('properties-panel');
    if (propertiesPanel) {
      propertiesPanel.style.display = 'none';
    }

    // Remove existing amenities panel
    const existingPanel = document.getElementById('amenities-panel');
    if (existingPanel) {
      existingPanel.remove();
    }

    // Create compact amenities panel
    const amenitiesPanel = document.createElement('div');
    amenitiesPanel.id = 'amenities-panel';
    amenitiesPanel.className = 'amenities-panel-compact';

    // Sort amenities by distance
    const sortedAmenities = amenities.sort((a, b) => parseFloat(a.distance_km) - parseFloat(b.distance_km));

    // Get amenity configuration
    const amenityConfig = getAmenityConfig(amenityType);

    // Create compact amenities list
    const amenitiesList = sortedAmenities.map((amenity, index) => `
      <div class="amenity-item-compact" onclick="navigateToAmenity(${amenity.longitude}, ${amenity.latitude}, '${amenity.name.replace(/'/g, "\\'")}')">
        <div class="amenity-content">
          <div class="amenity-name-compact">${amenity.name}</div>
          <div class="amenity-distance-compact">${amenity.distance_km} km away</div>
        </div>
      </div>
    `).join('');

    amenitiesPanel.innerHTML = `
      <div class="amenities-header-compact">
        <div class="header-info-compact">
          <div class="header-text-compact">
            <h3 class="amenities-title-compact">${amenityConfig.label}</h3>
            <p class="amenities-count-compact">${sortedAmenities.length} nearby</p>
          </div>
        </div>
        <button class="close-btn-compact" onclick="window.clearAmenities()">✕</button>
      </div>
      
      <div class="amenities-scroll-container">
        ${amenitiesList}
      </div>
      
      <div class="amenities-footer-compact">
        <div class="footer-stat">
          <span class="stat-label-small">Nearest:</span>
          <span class="stat-value-small">${sortedAmenities[0]?.distance_km || 'N/A'} km</span>
        </div>
        <div class="footer-divider"></div>
        <div class="footer-stat">
          <span class="stat-label-small">Average:</span>
          <span class="stat-value-small">${calculateAverageDistance(sortedAmenities)}</span>
        </div>
      </div>
    `;

    document.body.appendChild(amenitiesPanel);

    // Animate panel in
    setTimeout(() => {
      amenitiesPanel.classList.add('panel-visible');
    }, 50);
  }

  function resetAmenityButtons(activeType = null, count = null) {
    const amenityIcons = {
      hospitals: '🏥',
      schools: '🏫',
      malls: '🏪',
      restaurants: '🍽️',
      banks: '🏦',
      parks: '🏞️',
      metro: '🚇'
    };

    const amenityLabels = {
      hospitals: 'Hospitals',
      schools: 'Schools',
      malls: 'Malls',
      restaurants: 'Food',
      banks: 'Banks',
      parks: 'Parks',
      metro: 'Metro'
    };

    const buttons = document.querySelectorAll('.amenity-btn');
    buttons.forEach(btn => {
      const type = btn.dataset.amenity;
      const icon = amenityIcons[type] || '📍';
      const label = amenityLabels[type] || type;

      // Always show clean button without count
      btn.innerHTML = `
        <span class="btn-icon">${icon}</span>
        <span class="btn-label">${label}</span>
      `;

      // Highlight active button
      if (type === activeType) {
        btn.style.background = 'var(--gold-pale)';
        btn.style.borderColor = 'var(--gold-light)';
        btn.style.color = 'var(--gold-mid)';
      } else {
        btn.style.background = 'rgba(255, 255, 255, 0.03)';
        btn.style.borderColor = 'var(--border-subtle)';
        btn.style.color = 'var(--t2)';
      }

      btn.disabled = false;
    });
  }

  // Add event listeners to amenity buttons (delegated)
  document.addEventListener('click', (e) => {
    // Amenity Buttons
    const amenityBtn = e.target.closest('.amenity-btn');
    if (amenityBtn) {
      const amenityType = amenityBtn.dataset.amenity;

      // Check if insights data is loaded
      if (!window.insightsData || !Array.isArray(window.insightsData)) {
        console.log('ℹ️ Location data still loading...');
        return;
      }

      if (currentLocationId) {
        // Double-check that we have valid location data before proceeding
        const locationData = window.insightsData.find(d => d.location_id === currentLocationId);
        if (!locationData || !locationData.latitude || !locationData.longitude) {
          console.log('ℹ️ Please select a location on the map first');
          return;
        }

        displayAmenitiesOnMap(currentLocationId, amenityType);
      } else {
        console.log('ℹ️ Please select a location on the map first');
      }
    }

    // Clear Amenities Button
    if (e.target.closest('#clear-amenities-btn')) {
      clearAmenities();
    }

    // Close Amenities Card Button
    const closeAmenitiesBtn = e.target.closest('#close-amenities');
    if (closeAmenitiesBtn) {
      document.getElementById('amenities-list-card').style.display = 'none';
    }
  });





  // Interaction for Flood and Rainfall layers
  const interactiveLayers = ['location-core', 'flood-points-layer', 'rainfall-layer'];

  interactiveLayers.forEach(layerId => {
    map.on('mouseenter', layerId, () => {
      map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', layerId, () => {
      map.getCanvas().style.cursor = '';
    });
  });

  map.on('click', (e) => {
    const features = map.queryRenderedFeatures(e.point, {
      layers: ['flood-points-layer', 'rainfall-layer']
    });

    if (features.length > 0) {
      // Check if floods checkbox is checked
      const floodsCheckbox = document.querySelector('input[type="checkbox"][id*="flood"]');
      if (!floodsCheckbox || !floodsCheckbox.checked) {
        return; // Don't show intel card if floods are not enabled
      }

      const feature = features[0];
      const props = feature.properties;
      const card = document.getElementById("intel-card");

      card.style.display = "flex";

      let insightHtml = "";
      if (feature.layer.id === 'rainfall-layer') {
        insightHtml = `
          <div style="padding: 18px;">
            <p style="color: var(--text-400); font-size: 10px; text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 1.5px; font-weight: 700;">Rainfall</p>
            <h3 style="font-size: 2.8rem; font-weight: 800; margin: 0 0 6px 0; color: var(--text-100); letter-spacing: -2px;">${props.rainfall_mm}<span style="font-size:1rem;font-weight:600;color:var(--text-300);margin-left:6px;">mm</span></h3>
            
            <div style="display: flex; flex-direction: column; gap: 12px; border-top: 1px solid var(--border-subtle); padding-top: 16px; margin-top: 16px;">
              <div style="display: flex; justify-content: space-between; gap: 12px;">
                <span style="color: var(--text-400); font-size: 12px;">AWS Location</span>
                <span style="color: var(--text-100); font-size: 12px; font-weight: 600; text-align: right;">${props.location}</span>
              </div>
              <div style="display: flex; justify-content: space-between; gap: 12px;">
                <span style="color: var(--text-400); font-size: 12px;">Mandal</span>
                <span style="color: var(--text-100); font-size: 12px; font-weight: 600; text-align: right;">${props.mandal}</span>
              </div>
            </div>

            <p style="margin-top: 16px; font-size: 11px; color: var(--text-400); line-height: 1.6; padding: 10px 12px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: 10px;">
              Reference data from TS Development Planning Society. Values represent 24-hour cumulative rainfall depth.
            </p>
          </div>
        `;
      } else {
        insightHtml = `
          <div style="padding: 18px;">
            <p style="color: var(--text-400); font-size: 10px; text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 1.5px; font-weight: 700;">GHMC Monsoon Report</p>
            <h3 style="font-size: 1.5rem; font-weight: 800; margin: 0 0 16px 0; color: #EF4444; letter-spacing: -0.3px;">⚠️ Water Stagnation</h3>
            
            <div style="border-top: 1px solid var(--border-subtle); padding-top: 14px;">
              <div style="color: var(--text-400); font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 8px;">Observation Address</div>
              <div style="color: var(--text-100); font-size: 13px; font-weight: 500; line-height: 1.5;">${props.address}</div>
            </div>

            <div style="margin-top: 16px; padding: 12px; background: rgba(185, 28, 28, 0.05); border-radius: 10px; border: 1px solid rgba(185, 28, 28, 0.12);">
              <p style="margin: 0; font-size: 11px; color: var(--negative); line-height: 1.5; font-weight: 500;">Historical area of concern. Vigilance advised during heavy rains.</p>
            </div>
          </div>
        `;
      }

      card.innerHTML = insightHtml;

      map.easeTo({
        center: feature.geometry.coordinates,
        zoom: 15,
        duration: 800
      });
      return; // Stop default location click logic
    }
  });

  map.on("click", e => {
    try {
      // Don't close if clicking on location main markers OR amenity markers
      const clickedLocation = map.queryRenderedFeatures(e.point, { layers: ["location-core"] }).length > 0;
      let clickedAmenity = false;

      if (map.getLayer("amenity-markers")) {
        clickedAmenity = map.queryRenderedFeatures(e.point, { layers: ["amenity-markers"] }).length > 0;
      }

      if (!clickedLocation && !clickedAmenity) {
        // Drop / move logic removed as requested by USER
        const lngLat = e.lngLat;
        // Marker creation suppressed

        // Close Popup if clicking elsewhere
        if (currentPopup) {
          currentPopup.remove();
          currentPopup = null;
          // If we just closed a popup, do we want to clear the whole amenity layer?
          // If YES, let code proceed. If NO, return here.
          // For now, let's keep amenities visible but close the popup.
        }

        // USER EXPLORING MODE: Don't close card if amenities are active
        if (currentAmenityLayer) return;

        // Title visibility logic removed
        document.getElementById("intel-card").style.display = "none";

        if (typeof activeMarker !== 'undefined' && activeMarker) {
          activeMarker.remove();
        }

        // Clear amenities if map is clicked elsewhere
        if (currentAmenityLayer) {
          clearAmenities(); // Use the helper function!
        }
      }
    } catch (err) {
      console.error("Error in map click handler:", err);
    }
  });
});

// NEW STRUCTURED PROJECT FUNCTIONS
function createProjectGroupCard(project) {
  const card = document.createElement('div');
  card.className = 'prop-card';

  // Parse images for thumbnail
  let imageUrl = null;
  if (project.images) {
    try {
      const images = JSON.parse(project.images);
      if (Array.isArray(images) && images.length > 0) {
        imageUrl = images[0];
      }
    } catch (e) {
      console.warn('Failed to parse images:', e);
    }
  }

  // Get unique BHK types and price range
  const bhkTypes = [...new Set(project.properties.map(p => p.bhk).filter(Boolean))]
    .map(bhk => parseFloat(bhk) % 1 === 0 ? parseInt(bhk) : parseFloat(bhk))
    .sort((a, b) => a - b);
  const prices = project.properties
    .map(p => p.price_per_sft)
    .filter(p => p && p > 0)
    .sort((a, b) => a - b);

  const priceText = prices.length > 0
    ? prices.length === 1
      ? `₹${Math.round(prices[0]).toLocaleString()}/sqft`
      : `₹${Math.round(prices[0]).toLocaleString()} - ${Math.round(prices[prices.length - 1]).toLocaleString()}/sqft`
    : 'Price on request';

  // Status badge color
  let statusClass = 'prop-tag-status';
  if (project.construction_status) {
    const status = project.construction_status.toLowerCase();
    if (status.includes('rtm') || status.includes('ready')) {
      statusClass = 'prop-tag-status';
    } else if (status.includes('under') || status.includes('construction')) {
      statusClass = 'prop-tag-avail';
    }
  }

  // Create BHK badges HTML with variations
  const bhkBadgesHtml = bhkTypes.map(bhk => {
    // Get all properties of this BHK type
    const bhkProperties = project.properties.filter(p => {
      const propBhk = parseFloat(p.bhk) % 1 === 0 ? parseInt(p.bhk) : parseFloat(p.bhk);
      return propBhk === bhk;
    });

    // Get unique facings for this BHK type
    const facings = [...new Set(bhkProperties.map(p => p.full_details?.facing).filter(Boolean))];

    // Create the badge text
    let badgeText = `${bhk} BHK`;
    if (facings.length > 0) {
      badgeText += ` (${facings.join(', ')})`;
    }

    return `<span class="bhk-badge">${badgeText}</span>`;
  }).join('');

  card.innerHTML = `
      ${imageUrl
      ? `<img src="${imageUrl}" alt="${project.projectname}" class="prop-card-thumb" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />`
      : ''
    }
      <div class="prop-card-thumb-placeholder" style="${imageUrl ? 'display:none;' : ''}">🏢</div>
      
      <div class="prop-card-body">
        <h3 class="prop-card-name">${project.projectname}</h3>
        <p class="prop-card-builder">by ${project.buildername || 'Builder not specified'}</p>
        
        <!-- BHK Configuration Badges -->
        <div class="bhk-badges-container">
          ${bhkBadgesHtml}
        </div>
        
        <div class="prop-card-details">
          <div class="prop-detail-row">
            <span class="prop-detail-label">Type:</span>
            <span class="prop-detail-value">${project.project_type || 'N/A'}</span>
          </div>
          <div class="prop-detail-row">
            <span class="prop-detail-label">Sizes:</span>
            <span class="prop-detail-value">${project.properties.length} projects</span>
          </div>
          <div class="prop-detail-row">
            <span class="prop-detail-label">₹/sqft:</span>
            <span class="prop-detail-value prop-price">${priceText}</span>
          </div>
          ${project.construction_status ? `
          <div class="prop-detail-row">
            <span class="prop-detail-label">Status:</span>
            <span class="prop-detail-value">
              <span class="prop-tag ${statusClass}">${project.construction_status}</span>
            </span>
          </div>
          ` : ''}
          <div class="prop-detail-row">
            <span class="prop-detail-label">Area:</span>
            <span class="prop-detail-value">
              <span class="prop-tag prop-tag-area">${project.areaname || 'N/A'}</span>
            </span>
          </div>
        </div>
      </div>
    `;

  // Click handler to show all configurations and navigate to property on map with 3D view
  card.onclick = () => {
    showProjectConfigurations(project);
    
    // Navigate map to property location with 3D front-side view
    if (project.properties && project.properties.length > 0) {
      const prop = project.properties[0];
      const coords = extractCoordinates(prop.google_place_location || prop.google_maps_location);
      
      if (coords && map) {
        map.flyTo({
          center: [coords.lng, coords.lat],
          zoom: 15, // Neighborhood level zoom
          pitch: 60, // Tilt to see buildings in 3D (0-85 degrees)
          bearing: 0, // Face north (adjust based on property orientation)
          duration: 2000,
          essential: true
        });
      }
    }
  };

  return card;
}

function showProjectConfigurations(project) {
  const listContainer = document.getElementById('prop-list');

  // Store the current projects list for back navigation
  if (!window.currentProjectsList) {
    window.currentProjectsList = Array.from(listContainer.children);
  }

  // Store project data for fallback
  window.currentProject = project;

  // Skip the intermediate BHK selection — go directly to full property details
  showPropertyDetails(project.properties[0]);
}

// Helper function to show property details by ID - make it globally accessible
window.showPropertyDetailsFromTable = function (propertyId) {
  callSupabaseRPC('get_property_by_id_func', { prop_id: propertyId })
    .then(data => {
      // Handle Supabase RPC response format (returns array)
      const property = Array.isArray(data) && data.length > 0 ? data[0] : data;
      showPropertyDetails(property);
    })
    .catch(err => {
      console.error('Failed to load property:', err);
      alert('Failed to load property details. Please try again.');
    });
};

function showPropertyDetails(property) {
  const listContainer = document.getElementById('prop-list');
  const countEl = document.getElementById('prop-panel-count');

  // Clear any existing routes and markers from previous property
  clearRoutes();
  
  // Store the current property for commute calculator
  window.currentPropertyDetails = property;
  
  const details = property.full_details;
  
  // Store coordinates - try multiple sources
  let lat = null, lng = null;
  
  // 1. Try latitude/longitude fields directly (if they exist in full_details)
  if (details && details.latitude && details.longitude) {
    lat = parseFloat(details.latitude);
    lng = parseFloat(details.longitude);
    console.log('✅ Got coordinates from latitude/longitude fields:', lat, lng);
  }
  
  // 2. Try extracting from google_place_location or google_maps_location
  if (!lat || !lng) {
    const locationStr = property.google_place_location || property.google_maps_location || 
                       details?.google_place_location || details?.google_maps_location;
    if (locationStr) {
      const coords = extractCoordinates(locationStr);
      if (coords) {
        lat = coords.lat;
        lng = coords.lng;
        console.log('✅ Extracted coordinates from location string:', lat, lng);
      }
    }
  }
  
  // Store coordinates if we found them
  if (lat && lng && !isNaN(lat) && !isNaN(lng)) {
    window.currentPropertyLocation = { lat, lng };
    console.log('✅ Stored property coordinates:', window.currentPropertyLocation);
  } else {
    window.currentPropertyLocation = null;
    console.warn('⚠️ No valid coordinates found for property');
    console.warn('⚠️ property.google_place_location:', property.google_place_location);
    console.warn('⚠️ property.google_maps_location:', property.google_maps_location);
    console.warn('⚠️ details:', details);
  }
  
  // Debug: Log property structure
  console.log('🏠 showPropertyDetails called with property:', property);
  console.log('🏠 property.id:', property.id);
  console.log('🏠 property.full_details:', property.full_details);
  console.log('🏠 property.full_details.latitude:', property.full_details?.latitude);
  console.log('🏠 property.full_details.longitude:', property.full_details?.longitude);

  // Store the current configurations list for back navigation
  if (!window.currentConfigsList) {
    window.currentConfigsList = {
      html: listContainer.innerHTML,
      count: countEl.innerHTML
    };
  }
  
  // Get property ID - could be at top level or in full_details
  const propertyId = property.id || (details && details.id) || 'unknown';

  // Update header with back button — goes straight to projects list
  countEl.innerHTML = `<button onclick="window.goBackToProjects()" style="background:none;border:none;color:var(--gold-mid);cursor:pointer;font-size:0.9rem;font-weight:600;">← Back to Projects</button>`;

  // Parse images for gallery
  let images = [];
  if (details.images) {
    try {
      images = JSON.parse(details.images);
      if (!Array.isArray(images)) images = [];
    } catch (e) {
      images = [];
    }
  }

  // Build gallery HTML — horizontal scroll strip to avoid vertical gap
  let galleryHTML = '';
  if (images.length > 0) {
    galleryHTML = `
          <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;margin-bottom:16px;scrollbar-width:thin;">
            ${images.map(img => `
              <img src="${img}" alt="${details.projectname}"
                style="height:160px;min-width:220px;max-width:260px;object-fit:cover;border-radius:10px;flex-shrink:0;border:1px solid rgba(201,162,74,0.2);"
                onerror="this.style.display='none'" />
            `).join('')}
          </div>
        `;
  }


  // Helper function to format field value
  const formatField = (value, type = 'text') => {
    if (!value || value === 'null' || value === 'None' || value === '' || value === 'N/A' || value === 0) return null;
    if (type === 'price' && typeof value === 'number') {
      return `₹${(value / 10000000).toFixed(2)} Cr`;
    }
    if (type === 'sqft-price' && typeof value === 'number') {
      return `₹${Math.round(value).toLocaleString()}/sqft`;
    }
    if (type === 'bhk' && typeof value === 'number') {
      return `${Math.floor(value)} BHK`;
    }
    return value;
  };

  // Helper function to render a field
  const renderField = (label, value, type = 'text') => {
    const formatted = formatField(value, type);
    if (!formatted) return '';
    return `<div class="detail-field-inline"><label>${label}</label><span>${formatted}</span></div>`;
  };

  // Helper to render a section only if it has content
  const renderSection = (title, fields) => {
    const content = fields.filter(f => f).join('');
    if (!content) return '';
    return `<div class="detail-section-inline"><h3>${title}</h3>${content}</div>`;
  };

  // Get available BHK types for this project
  // First try to get from stored project, otherwise derive from current location properties
  let availableBhks = [];

  if (window._bhkProject) {
    availableBhks = [...new Set(window._bhkProject.properties.map(p => p.bhk).filter(Boolean))]
      .map(bhk => parseFloat(bhk) % 1 === 0 ? parseInt(bhk) : parseFloat(bhk))
      .sort((a, b) => a - b);
  } else if (window.allLocationProperties) {
    // Get BHKs from all properties in current location that match this project
    const projectProperties = window.allLocationProperties.filter(p =>
      p.projectname === property.projectname && p.buildername === property.buildername
    );
    availableBhks = [...new Set(projectProperties.map(p => p.bhk).filter(Boolean))]
      .map(bhk => parseFloat(bhk) % 1 === 0 ? parseInt(bhk) : parseFloat(bhk))
      .sort((a, b) => a - b);
  }

  // Create BHK clarification note
  const bhkNote = availableBhks.length > 1 ?
    `<div style="background:rgba(201,162,74,0.08);border:1px solid rgba(201,162,74,0.2);border-radius:8px;padding:10px;margin-bottom:16px;font-size:12px;color:var(--t2);">
      <strong>Note:</strong> The data below represents information for all available configurations: ${availableBhks.join(', ')} BHK
    </div>` : '';

  // Build the complete property details HTML with ALL 64+ fields
  const detailsHTML = `
        <div class="property-detail-inline">
          <h2>${details.projectname || 'Unnamed Project'}</h2>
          <p style="color:var(--t2);margin:0 0 12px 0;">by ${details.buildername || 'Builder not specified'}</p>
          
          <!-- Inline Commute Calculator -->
          <div class="commute-inline-section" style="background:rgba(166,138,61,0.08);border:1px solid rgba(166,138,61,0.2);border-radius:10px;padding:16px;margin-bottom:16px;">
            <h3 style="margin:0 0 12px 0;font-size:14px;color:var(--gold-mid);display:flex;align-items:center;gap:8px;">
              🚗 Calculate Commute
            </h3>
            <input 
              type="text" 
              id="commute-inline-search-${propertyId}"
              placeholder="Search for your office location..."
              style="width:100%;padding:10px;border:1px solid rgba(166,138,61,0.3);border-radius:8px;background:white;font-size:13px;margin-bottom:8px;"
              oninput="searchOfficeInline(${propertyId}, this.value)"
              autocomplete="off"
            />
            <div id="commute-inline-suggestions-${propertyId}" class="office-suggestions-inline"></div>
            <div id="commute-inline-routes-${propertyId}" class="commute-routes-inline" style="display:none;margin-top:12px;"></div>
          </div>

          <!-- Connectivity Button -->
          <div class="connectivity-section" style="background:rgba(65,105,225,0.08);border:1px solid rgba(65,105,225,0.2);border-radius:10px;padding:16px;margin-bottom:16px;">
            <button 
              id="connectivity-btn-${propertyId}"
              onclick="window.showConnectivityForProperty('${propertyId}')"
              style="width:100%;padding:12px;background:linear-gradient(135deg,#4169E1,#1E90FF);color:white;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;"
            >
              🚉 Show Connectivity
            </button>
            <div id="connectivity-results-${propertyId}" style="display:none;margin-top:12px;"></div>
          </div>
          
          ${bhkNote}
          ${galleryHTML}
          
          ${renderSection('🏠 Basic Info', [
    renderField('Project Name', details.projectname),
    renderField('Builder', details.buildername),
    renderField('Type', details.project_type),
    renderField('Community', details.communitytype),
    renderField('Status', details.status),
    renderField('Project Status', details.project_status),
    renderField('Availability', details.isavailable === 'No' ? 'Sold Out' : (details.isavailable === 'Yes' ? 'Available' : details.isavailable))
  ])}
          
          ${renderSection('📍 Location', [
    renderField('Area', details.areaname),
    renderField('Location', details.projectlocation),
    renderField('Google Name', details.google_place_name),
    renderField('Full Address', details.google_place_address),
    renderField('Maps Link', details.google_maps_location ? `<a href="${details.google_maps_location}" target="_blank" style="color:var(--gold-mid);">View on Maps</a>` : null),
    renderField('Open in Maps', details.mobile_google_map_url ? `<a href="${details.mobile_google_map_url}" target="_blank" style="color:var(--gold-mid);">Open</a>` : null)
  ])}
          
          ${renderSection('💰 Pricing', [
    renderField('Base Price', details.baseprojectprice, 'price'),
    renderField('Price / sqft', details.price_per_sft, 'sqft-price'),
    renderField('Total Buildup Area', details.total_buildup_area),
    renderField('Price Last Updated', details.price_per_sft_update_date),
    renderField('Floor Rise Charges', details.floor_rise_charges),
    renderField('Floor Rise ₹/floor', details.floor_rise_amount_per_floor),
    renderField('Applicable Above Floor', details.floor_rise_applicable_above_floor_no),
    renderField('Facing Charges', details.facing_charges),
    renderField('PLC', details.preferential_location_charges),
    renderField('PLC Conditions', details.preferential_location_charges_conditions),
    renderField('Extra Parking Cost', details.amount_for_extra_car_parking)
  ])}
          
          ${renderSection('🏗️ Project Details', [
    renderField('Launch Date', details.project_launch_date),
    renderField('Possession Date', details.possession_date),
    renderField('Construction Status', details.construction_status),
    renderField('Material', details.construction_material),
    renderField('Land Area', details.total_land_area),
    renderField('Towers', details.number_of_towers),
    renderField('Floors', details.number_of_floors),
    renderField('Flats/Floor', details.number_of_flats_per_floor),
    renderField('Total Sizes', details.total_number_of_units),
    renderField('Open Space %', details.open_space),
    renderField('Carpet Area %', details.carpet_area_percentage),
    renderField('Floor-to-Ceiling Height', details.floor_to_ceiling_height)
  ])}
          
          ${renderSection('🛏️ Unit Configuration', [
    renderField('BHK Config', details.bhk, 'bhk'),
    renderField('Area (sqft)', details.sqfeet),
    renderField('Area (sqyard)', details.sqyard),
    renderField('Facing', details.facing),
    renderField('Car Parkings', details.no_of_car_parkings)
  ])}
          
          ${renderSection('🏊 Amenities & Specs', [
    renderField('External Amenities', details.external_amenities),
    renderField('Specification', details.specification),
    renderField('Power Backup', details.powerbackup),
    renderField('Passenger Lifts', details.no_of_passenger_lift),
    renderField('Service Lifts', details.no_of_service_lift),
    renderField('Visitor Parking', details.visitor_parking),
    renderField('Ground Vehicle Movement', details.ground_vehicle_movement),
    renderField('Main Door Height', details.main_door_height),
    renderField('Home Loan', details.home_loan),
    renderField('Banks for Loan', details.available_banks_for_loan)
  ])}
          
          ${renderSection('👷 Builder Profile', [
    renderField('Years in Business', details.builder_age),
    renderField('Completed Projects', details.builder_completed_properties),
    renderField('Ongoing Projects', details.builder_ongoing_projects),
    renderField('Upcoming Projects', details.builder_upcoming_properties),
    renderField('Total Projects', details.builder_total_properties),
    renderField('Operating Cities', details.builder_operating_locations),
    renderField('Headquarters', details.builder_origin_city)
  ])}
        </div>
      `;

  listContainer.innerHTML = detailsHTML;
}

// Function to go back to configurations
window.goBackToConfigurations = function () {
  const listContainer = document.getElementById('prop-list');
  const countEl = document.getElementById('prop-panel-count');

  if (window.currentConfigsList) {
    // Re-render the configurations instead of restoring HTML
    // This ensures click handlers are properly attached
    if (window.currentProject) {
      showProjectConfigurations(window.currentProject);
    } else {
      // Fallback to stored HTML if project data not available
      listContainer.innerHTML = window.currentConfigsList.html;
      countEl.innerHTML = window.currentConfigsList.count;
    }
    window.currentConfigsList = null;
  }
};

function closePropertyDetail() {
  // Clear routes and markers when closing property details
  clearRoutes();
  
  document.getElementById('property-detail-drawer').classList.remove('open');
  document.getElementById('properties-panel').classList.remove('detail-open');
}

// Global function for back navigation
window.goBackToProjects = function () {
  const listContainer = document.getElementById('prop-list');
  const countEl = document.getElementById('prop-panel-count');

  if (window.currentProjectsList) {
    // Restore the original projects list
    listContainer.innerHTML = '';
    window.currentProjectsList.forEach(child => {
      listContainer.appendChild(child);
    });

    // Restore the count
    const projectCount = window.currentProjectsList.length;
    countEl.textContent = `${projectCount} project${projectCount !== 1 ? 's' : ''}`;

    // Clear navigation state
    window.currentProjectsList = null;
    window.currentProject = null;
  }
};


// ── AREA FILTER: show only lead-specific locations ────────────────────────
function applyAreaFilter(areas) {
  if (!areas || !areas.length) return;
  const normalizedAreas = areas.map(a => a.toLowerCase().trim());
  // Filter both layers to show only the matching location pins
  const filterExpr = ['in', ['downcase', ['get', 'location']], ['literal', normalizedAreas]];
  if (map.getLayer('location-core')) map.setFilter('location-core', filterExpr);
  if (map.getLayer('location-glow')) map.setFilter('location-glow', filterExpr);
  // Auto-fit the map to the filtered locations
  if (!window.insightsData || !Array.isArray(window.insightsData)) return;
  const matches = window.insightsData.filter(d =>
    normalizedAreas.includes((d.location || '').toLowerCase().trim())
  );
  if (!matches.length) return;
  if (matches.length === 1) {
    map.flyTo({ center: [matches[0].longitude, matches[0].latitude], zoom: 13.5, duration: 1500 });
  } else {
    const bounds = new maplibregl.LngLatBounds();
    matches.forEach(loc => bounds.extend([loc.longitude, loc.latitude]));
    map.fitBounds(bounds, { padding: 100, maxZoom: 14, duration: 1500 });
  }
  console.log(`Map filtered to ${matches.length} location(s):`, areas);
}

// Make function globally accessible
window.applyAreaFilter = applyAreaFilter;

// ── INJECTED PROPERTIES: render parent's exact lead-matched data directly ──
function renderInjectedProperties(projects) {
  const listContainer = document.getElementById('prop-list');
  const countEl = document.getElementById('prop-panel-count');
  const loadingEl = document.getElementById('prop-loading');
  const panel = document.getElementById('properties-panel');
  if (!listContainer || !countEl) return;

  if (loadingEl) loadingEl.style.display = 'none';
  if (panel) panel.classList.add('open');
  listContainer.innerHTML = '';

  if (!projects || projects.length === 0) {
    listContainer.innerHTML = `<div class="prop-empty"><div class="prop-empty-icon">🏢</div><p>No lead-matched properties in this location</p></div>`;
    countEl.textContent = '0 projects (lead-matched)';
    return;
  }

  countEl.textContent = `${projects.length} project${projects.length !== 1 ? 's' : ''} (lead-matched)`;
  projects.forEach(project => {
    const card = createProjectGroupCard(project);
    listContainer.appendChild(card);
  });
}
window.renderInjectedProperties = renderInjectedProperties;

// ── RERA FILTER: filter properties panel to lead-specific matched projects ──
function applyReraFilterToPanel(normalizedReras, normalizedProjectNames) {
  if (!window.allLocationProperties) return;
  const listContainer = document.getElementById('prop-list');
  const countEl = document.getElementById('prop-panel-count');
  if (!listContainer || !countEl) return;

  let properties = window.allLocationProperties;

  // Filter by RERA (primary) or project name (fallback for properties without RERA)
  const hasFilter = (normalizedReras && normalizedReras.length > 0) || (normalizedProjectNames && normalizedProjectNames.length > 0);
  if (hasFilter) {
    properties = properties.filter(prop => {
      const rera = ((prop.full_details && prop.full_details.rera_number) || '').toLowerCase().trim();
      if (rera && normalizedReras && normalizedReras.includes(rera)) return true;
      const name = (prop.projectname || '').toLowerCase().trim();
      if (name && normalizedProjectNames && normalizedProjectNames.includes(name)) return true;
      return false;
    });
  }

  // Re-group by project + builder
  const projectGroups = {};
  properties.forEach(property => {
    const projectKey = `${property.projectname || 'Unnamed Project'}_${property.buildername || 'Unknown Builder'}`;
    if (!projectGroups[projectKey]) {
      projectGroups[projectKey] = {
        projectname: property.projectname || 'Unnamed Project',
        buildername: property.buildername,
        project_type: property.project_type,
        construction_status: property.construction_status,
        areaname: property.areaname,
        images: property.images,
        properties: []
      };
    }
    projectGroups[projectKey].properties.push(property);
  });

  const projects = Object.values(projectGroups).sort((a, b) => b.properties.length - a.properties.length);

  listContainer.innerHTML = '';
  if (projects.length === 0) {
    listContainer.innerHTML = `<div class="prop-empty"><div class="prop-empty-icon">🏢</div><p>No lead-matched properties in this location</p></div>`;
    countEl.textContent = '0 projects (lead-matched)';
    return;
  }

  const label = hasFilter ? ' (lead-matched)' : '';
  countEl.textContent = `${projects.length} project${projects.length !== 1 ? 's' : ''}${label}`;
  projects.forEach(project => {
    const card = createProjectGroupCard(project);
    listContainer.appendChild(card);
  });
}
window.applyReraFilterToPanel = applyReraFilterToPanel;

// ── POSTMESSAGE LISTENER: receive filter from Expert Dashboard iframe ──────
window.addEventListener('message', (event) => {
  if (!event.origin.includes('localhost') && !event.origin.includes('relai')) return;
  if (!event.data || event.data.type !== 'RELAI_FILTER') return;
  const { areas = [], reras = [], injectedProperties = [] } = event.data;
  if (!areas.length) return;
  console.log('RELAI_FILTER received from parent:', areas, '| RERAs:', reras.length, '| Injected:', injectedProperties.length);

  // Store injected properties indexed by area (lowercase) for use in loadPropertiesForLocation
  if (injectedProperties.length > 0) {
    window._relaiInjectedByArea = {};
    injectedProperties.forEach(p => {
      const area = (p.areaname || '').toLowerCase().trim();
      if (!area) return;
      if (!window._relaiInjectedByArea[area]) window._relaiInjectedByArea[area] = [];
      window._relaiInjectedByArea[area].push(p);
    });
  } else {
    window._relaiInjectedByArea = null;
  }

  // If layers are already ready, apply immediately; otherwise store for when they load
  if (map.getLayer('location-core')) {
    applyAreaFilter(areas);
  } else {
    window._relaiFilterAreas = areas;
  }

  // If the properties panel is already open for a location, re-render with injected data
  if (window._relaiCurrentLocation && window._relaiInjectedByArea) {
    const key = window._relaiCurrentLocation.toLowerCase().trim();
    const locationProjects = window._relaiInjectedByArea[key];
    if (locationProjects) renderInjectedProperties(locationProjects);
  }
});



// ═══════════════════════════════════════════════════════════════════════════
// FUTURE INSIGHTS FEATURE
// ═══════════════════════════════════════════════════════════════════════════

let locationDevelopmentsData = null;
let currentFILocation = null;
let currentFIYear = null;

// Load location developments data
async function loadLocationDevelopments() {
  if (locationDevelopmentsData) return locationDevelopmentsData;
  
  try {
    const response = await fetch('location_developments.json');
    locationDevelopmentsData = await response.json();
    console.log('✅ Loaded location developments:', Object.keys(locationDevelopmentsData).length, 'locations');
    return locationDevelopmentsData;
  } catch (error) {
    console.error('❌ Error loading location developments:', error);
    return {};
  }
}

// Show Future Insights modal
async function showFutureInsights(locationId, locationName) {
  await loadLocationDevelopments();
  currentFILocation = locationId;
  
  const locationData = locationDevelopmentsData[locationId];
  if (!locationData || !locationData.developments) {
    alert('No development data available for this location');
    return;
  }
  
  // Update modal title
  document.getElementById('fi-modal-subtitle').textContent = locationName || locationData.location_name;
  
  // Extract all unique years
  const years = new Set();
  locationData.developments.forEach(dev => {
    if (dev.timeline && Array.isArray(dev.timeline)) {
      dev.timeline.forEach(timeRange => {
        const yearMatches = timeRange.match(/\d{4}/g);
        if (yearMatches) {
          yearMatches.forEach(year => years.add(parseInt(year)));
        }
      });
    }
  });
  
  const sortedYears = Array.from(years).sort();
  
  // Populate year timeline
  const timelineYears = document.getElementById('fi-timeline-years');
  timelineYears.innerHTML = '';
  
  sortedYears.forEach(year => {
    const count = countDevelopmentsForYear(locationData.developments, year);
    const yearItem = document.createElement('div');
    yearItem.className = 'fi-year-item';
    yearItem.textContent = year;
    yearItem.dataset.year = year;
    
    if (count > 0) {
      const countBadge = document.createElement('span');
      countBadge.className = 'fi-year-count';
      countBadge.textContent = count;
      yearItem.appendChild(countBadge);
    }
    
    yearItem.addEventListener('click', () => selectFIYear(year));
    timelineYears.appendChild(yearItem);
  });
  
  // Auto-select current year or first year
  const currentYear = new Date().getFullYear();
  const yearToSelect = sortedYears.includes(currentYear) ? currentYear : sortedYears[0];
  if (yearToSelect) {
    selectFIYear(yearToSelect);
  }
  
  // Show modal
  document.getElementById('fi-modal-overlay').style.display = 'flex';
}

// Count developments for a specific year
function countDevelopmentsForYear(developments, year) {
  return developments.filter(dev => {
    if (!dev.timeline) return false;
    return dev.timeline.some(timeRange => {
      const yearMatches = timeRange.match(/\d{4}/g);
      return yearMatches && yearMatches.some(y => parseInt(y) === year);
    });
  }).length;
}

// Select a year and show developments
function selectFIYear(year) {
  if (!currentFILocation || !locationDevelopmentsData) return;
  
  const locationData = locationDevelopmentsData[currentFILocation];
  if (!locationData) return;
  
  currentFIYear = year;
  
  // Update active year button
  document.querySelectorAll('.fi-year-item').forEach(item => {
    if (parseInt(item.dataset.year) === year) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
  
  // Filter developments for this year
  const developments = locationData.developments.filter(dev => {
    if (!dev.timeline) return false;
    return dev.timeline.some(timeRange => {
      const yearMatches = timeRange.match(/\d{4}/g);
      return yearMatches && yearMatches.some(y => parseInt(y) === year);
    });
  });
  
  // Update stats
  const highCert = developments.filter(d => d.certainty === 'High').length;
  const mediumCert = developments.filter(d => d.certainty === 'Medium' || d.certainty === 'Medium-High').length;
  
  document.getElementById('fi-stat-total').textContent = developments.length;
  document.getElementById('fi-stat-high').textContent = highCert;
  document.getElementById('fi-stat-medium').textContent = mediumCert;
  
  // Render development cards
  const content = document.getElementById('fi-modal-content');
  content.innerHTML = '';
  
  if (developments.length === 0) {
    content.innerHTML = `
      <div class="fi-empty-state">
        <h4>No developments found</h4>
        <p>No projects planned for ${year}</p>
      </div>
    `;
  } else {
    developments.forEach(dev => {
      const card = createFIDevCard(dev);
      content.appendChild(card);
    });
  }
}

// Create development card
function createFIDevCard(dev) {
  const card = document.createElement('div');
  card.className = 'fi-dev-card';
  
  const certClass = dev.certainty ? `fi-cert-${dev.certainty.toLowerCase().replace(/-/g, '-')}` : 'fi-cert-medium';
  
  card.innerHTML = `
    <div class="fi-dev-card-header">
      <h5 class="fi-dev-card-title">${dev.title || 'Untitled Development'}</h5>
      <div class="fi-dev-card-certainty">
        <span class="fi-cert-badge ${certClass}">${dev.certainty || 'Medium'}</span>
      </div>
    </div>
    
    <div class="fi-dev-card-timeline">
      ${dev.timeline && dev.timeline.length > 0 ? dev.timeline.map(t => {
        const years = t.match(/\d{4}/g);
        return `<span class="fi-timeline-chip">${years ? years.join('-') : t}</span>`;
      }).join('') : '<span class="fi-timeline-chip">Timeline TBD</span>'}
    </div>
    
    <div class="fi-dev-card-details">
      ${dev.context ? `
        <div class="fi-detail-section">
          <div class="fi-detail-label">📋 Context</div>
          <div class="fi-detail-text">${dev.context}</div>
        </div>
      ` : ''}
      
      ${dev.impact ? `
        <div class="fi-detail-section">
          <div class="fi-detail-label">💡 Impact</div>
          <div class="fi-detail-text">${dev.impact}</div>
        </div>
      ` : ''}
      
      ${dev.source ? `
        <div class="fi-detail-section">
          <div class="fi-detail-label">🔗 Source</div>
          <a href="https://${dev.source}" target="_blank" class="fi-source-link">
            ${dev.source}
          </a>
        </div>
      ` : ''}
    </div>
  `;
  
  // Toggle expand on click
  card.addEventListener('click', () => {
    card.classList.toggle('expanded');
  });
  
  return card;
}

// Hide Future Insights modal
function hideFutureInsights() {
  document.getElementById('fi-modal-overlay').style.display = 'none';
  currentFILocation = null;
  currentFIYear = null;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  // Sidebar toggle functionality
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  
  if (sidebarToggle && sidebar) {
    // Restore sidebar state from localStorage (default is open/visible)
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
      sidebar.classList.add('collapsed');
    }
    // If savedState is null or 'false', sidebar stays open (default)
    
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      
      // Store preference in localStorage
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('sidebarCollapsed', isCollapsed);
    });
  }
  
  // Close modal button
  const modalClose = document.getElementById('fi-modal-close');
  if (modalClose) {
    modalClose.addEventListener('click', hideFutureInsights);
  }
  
  // Close on overlay click
  const overlay = document.getElementById('fi-modal-overlay');
  if (overlay) {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        hideFutureInsights();
      }
    });
  }
  
  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.getElementById('fi-modal-overlay').style.display === 'flex') {
      hideFutureInsights();
    }
  });
});

// Export
window.showFutureInsights = showFutureInsights;
window.hideFutureInsights = hideFutureInsights;


// ===============================
// COMMUTE CALCULATOR
// ===============================

let currentPropertyLocation = null;
let currentRoutes = {};
let routeLayers = {};

window.openCommuteCalculator = function(lat, lng, propertyName) {
  console.log('🚗 Opening commute calculator for:', propertyName, 'at', lat, lng);
  currentPropertyLocation = { lat, lng, name: propertyName };
  
  const overlay = document.getElementById('commute-modal-overlay');
  const propertyNameEl = document.getElementById('commute-property-name');
  const routesSection = document.getElementById('commute-routes-section');
  const searchInput = document.getElementById('office-search-input');
  
  propertyNameEl.textContent = `From: ${propertyName}`;
  overlay.style.display = 'flex';
  routesSection.style.display = 'none';
  searchInput.value = '';
  
  // Clear previous routes
  clearRoutes();
};

// Helper function to open commute calculator from project card
window.openCommuteCalculatorFromProject = function(buttonEl, projectName) {
  // Find the project data
  const projects = window._propertyPinProjects || window.allLocationProperties || [];
  const project = projects.find(p => p.projectname === projectName);
  
  if (!project || !project.properties || project.properties.length === 0) {
    alert('Location coordinates not available for this property');
    return;
  }
  
  // Extract coordinates from first property
  const prop = project.properties[0];
  const coords = extractCoordinates(prop.google_place_location || prop.google_maps_location);
  
  if (!coords) {
    alert('Location coordinates not available for this property');
    return;
  }
  
  openCommuteCalculator(coords.lat, coords.lng, projectName);
};

// Helper function to open commute calculator from property details
window.openCommuteCalculatorFromProperty = function(propertyId, projectName) {
  // Find the property in allLocationProperties
  const properties = window.allLocationProperties || [];
  const property = properties.find(p => p.id === propertyId);
  
  if (!property) {
    alert('Property not found');
    return;
  }
  
  // Extract coordinates
  const coords = extractCoordinates(property.google_place_location || property.google_maps_location);
  
  if (!coords) {
    alert('Location coordinates not available for this property');
    return;
  }
  
  openCommuteCalculator(coords.lat, coords.lng, projectName);
};

// Inline commute calculator functions
window.searchOfficeInline = async function(propertyId, query) {
  if (!query || query.length < 3) {
    document.getElementById(`commute-inline-suggestions-${propertyId}`).innerHTML = '';
    return;
  }
  
  try {
    const response = await fetch(`${window.API_BASE_URL}/api/search-place?query=${encodeURIComponent(query)}`);
    const data = await response.json();
    
    if (data.success && data.suggestions.length > 0) {
      const suggestionsHTML = data.suggestions.map(s => `
        <div class="suggestion-item-inline" onclick="selectOfficeInline(${propertyId}, '${s.place_id}', '${s.description.replace(/'/g, "\\'")}')">
          <div style="font-weight:600;font-size:13px;">${s.main_text}</div>
          <div style="font-size:11px;color:var(--t3);">${s.secondary_text}</div>
        </div>
      `).join('');
      document.getElementById(`commute-inline-suggestions-${propertyId}`).innerHTML = suggestionsHTML;
    }
  } catch (error) {
    console.error('Error searching:', error);
  }
};

window.selectOfficeInline = async function(propertyId, placeId, description) {
  console.log('🔍 ========== selectOfficeInline START ==========');
  console.log('🔍 propertyId:', propertyId, 'type:', typeof propertyId);
  console.log('🔍 placeId:', placeId);
  console.log('🔍 description:', description);
  
  // First try to get property from stored currentPropertyDetails
  let property = window.currentPropertyDetails;
  console.log('📦 window.currentPropertyDetails:', property);
  
  // If not available or ID doesn't match, search in allLocationProperties
  if (!property || property.id !== propertyId) {
    console.log('⚠️ Property not in currentPropertyDetails or ID mismatch');
    const properties = window.allLocationProperties || [];
    console.log('📦 Searching in allLocationProperties, count:', properties.length);
    property = properties.find(p => p.id === propertyId);
    console.log('📦 Found in allLocationProperties:', !!property);
  }
  
  if (!property) {
    console.error('❌ Property not found with ID:', propertyId);
    console.log('Available properties:', window.allLocationProperties?.map(p => ({id: p.id, name: p.projectname})));
    document.getElementById(`commute-inline-routes-${propertyId}`).innerHTML = 
      '<div style="text-align:center;padding:12px;color:red;">Property not found (ID: ' + propertyId + ')</div>';
    return;
  }
  
  console.log('✅ Property found:', {
    id: property.id,
    projectname: property.projectname,
    google_place_location: property.google_place_location,
    google_maps_location: property.google_maps_location,
    full_details: property.full_details ? 'exists' : 'null'
  });
  
  // Extract coordinates - check both property and full_details
  let coords = null;
  const locInfo = property.google_place_location || 
                  property.google_maps_location ||
                  (property.full_details && property.full_details.google_place_location) ||
                  (property.full_details && property.full_details.google_maps_location);
  
  console.log('📍 locInfo:', locInfo);
  console.log('📍 locInfo type:', typeof locInfo);
  
  if (locInfo) {
    if (typeof locInfo === 'object' && locInfo !== null) {
      console.log('📍 locInfo is object, keys:', Object.keys(locInfo));
      if (locInfo.lat !== undefined && locInfo.lng !== undefined) {
        coords = { lat: parseFloat(locInfo.lat), lng: parseFloat(locInfo.lng) };
        console.log('📍 Extracted from object (lat/lng):', coords);
      } else if (locInfo.latitude !== undefined && locInfo.longitude !== undefined) {
        coords = { lat: parseFloat(locInfo.latitude), lng: parseFloat(locInfo.longitude) };
        console.log('📍 Extracted from object (latitude/longitude):', coords);
      }
    } else if (typeof locInfo === 'string') {
      console.log('📍 locInfo is string, attempting to parse');
      try {
        const parsed = JSON.parse(locInfo.replace(/'/g, '"'));
        console.log('📍 Parsed JSON:', parsed);
        if (parsed.lat !== undefined && parsed.lng !== undefined) {
          coords = { lat: parseFloat(parsed.lat), lng: parseFloat(parsed.lng) };
          console.log('📍 Extracted from parsed string (lat/lng):', coords);
        } else if (parsed.latitude !== undefined && parsed.longitude !== undefined) {
          coords = { lat: parseFloat(parsed.latitude), lng: parseFloat(parsed.longitude) };
          console.log('📍 Extracted from parsed string (latitude/longitude):', coords);
        }
      } catch (e) {
        console.error('❌ Error parsing coordinates:', e);
      }
    }
  }
  
  console.log('📍 Final extracted coords:', coords);
  
  if (!coords || !coords.lat || !coords.lng) {
    console.error('❌ No valid coordinates found');
    console.error('❌ coords object:', coords);
    document.getElementById(`commute-inline-routes-${propertyId}`).innerHTML = 
      '<div style="text-align:center;padding:12px;color:red;">Property location not available</div>';
    return;
  }
  
  console.log('✅ Using coordinates:', coords);
  
  // Clear suggestions
  document.getElementById(`commute-inline-suggestions-${propertyId}`).innerHTML = '';
  document.getElementById(`commute-inline-search-${propertyId}`).value = description;
  
  // Show loading
  const routesDiv = document.getElementById(`commute-inline-routes-${propertyId}`);
  routesDiv.style.display = 'block';
  routesDiv.innerHTML = '<div style="text-align:center;padding:12px;color:var(--t3);">Calculating routes...</div>';
  
  try {
    const url = `${window.API_BASE_URL}/api/directions?origin_lat=${coords.lat}&origin_lng=${coords.lng}&dest_place_id=${placeId}`;
    console.log('🌐 Fetching directions from:', url);
    
    const response = await fetch(url);
    const data = await response.json();
    
    console.log('📦 Directions response:', data);
    
    if (data.success && data.routes) {
      window.currentRoutes = data.routes;
      window.currentPropertyLocation = coords;
      console.log('✅ Routes received, calling displayRoutesInline');
      displayRoutesInline(propertyId, data.routes);
    } else {
      console.error('❌ No routes in response');
      routesDiv.innerHTML = `<div style="text-align:center;padding:12px;color:red;">Could not calculate routes: ${data.error || 'Unknown error'}</div>`;
    }
  } catch (error) {
    console.error('❌ Error fetching directions:', error);
    routesDiv.innerHTML = `<div style="text-align:center;padding:12px;color:red;">Error: ${error.message}</div>`;
  }
  
  console.log('🔍 ========== selectOfficeInline END ==========');
};

function displayRoutesInline(propertyId, routes) {
  const cardsHTML = [];
  
  if (routes.driving) {
    cardsHTML.push(`
      <div class="route-card-inline" onclick="drawRoute('driving')" style="cursor:pointer;">
        <div style="font-size:20px;">🚗</div>
        <div style="flex:1;">
          <div style="font-weight:600;font-size:12px;">Car</div>
          <div style="font-size:11px;color:var(--t3);">${routes.driving.distance} • ${routes.driving.duration_in_traffic}</div>
        </div>
      </div>
    `);
  }
  
  if (routes.transit) {
    cardsHTML.push(`
      <div class="route-card-inline" onclick="drawRoute('transit')" style="cursor:pointer;">
        <div style="font-size:20px;">🚇</div>
        <div style="flex:1;">
          <div style="font-weight:600;font-size:12px;">Transit</div>
          <div style="font-size:11px;color:var(--t3);">${routes.transit.distance} • ${routes.transit.duration}</div>
        </div>
      </div>
    `);
  }
  
  if (routes.bus) {
    cardsHTML.push(`
      <div class="route-card-inline" onclick="drawRoute('bus')" style="cursor:pointer;">
        <div style="font-size:20px;">🚌</div>
        <div style="flex:1;">
          <div style="font-weight:600;font-size:12px;">Bus</div>
          <div style="font-size:11px;color:var(--t3);">${routes.bus.distance} • ${routes.bus.duration}</div>
        </div>
      </div>
    `);
  }
  
  document.getElementById(`commute-inline-routes-${propertyId}`).innerHTML = cardsHTML.join('');
  
  // Auto-draw driving route
  drawRoute('driving');
}

// Helper function to extract coordinates
function extractCoordinates(locInfo) {
  if (!locInfo) return null;
  
  if (typeof locInfo === 'object') {
    if (locInfo.lat !== undefined && locInfo.lng !== undefined) 
      return { lat: parseFloat(locInfo.lat), lng: parseFloat(locInfo.lng) };
    if (locInfo.latitude !== undefined && locInfo.longitude !== undefined) 
      return { lat: parseFloat(locInfo.latitude), lng: parseFloat(locInfo.longitude) };
    return null;
  }
  
  const str = String(locInfo).trim();
  
  if (str.startsWith('{')) {
    try {
      const validJson = str.replace(/'/g, '"');
      const parsed = JSON.parse(validJson);
      if (parsed.lat !== undefined && parsed.lng !== undefined) 
        return { lat: parseFloat(parsed.lat), lng: parseFloat(parsed.lng) };
    } catch (e) { }
  }
  
  const urlMatch = str.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/) || 
                   str.match(/(?:q|query)=(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (urlMatch) return { lat: parseFloat(urlMatch[1]), lng: parseFloat(urlMatch[2]) };
  
  const rawMatch = str.match(/(-?\d+\.\d{3,})\s*,\s*(-?\d+\.\d{3,})/);
  if (rawMatch) return { lat: parseFloat(rawMatch[1]), lng: parseFloat(rawMatch[2]) };
  
  return null;
}

// ===================================================
//  CONNECTIVITY FUNCTION - Show nearest transport hubs
// ===================================================
window.showConnectivityForProperty = async function(propertyId) {
  console.log('🚉 showConnectivityForProperty called for propertyId:', propertyId);
  
  const resultsDiv = document.getElementById(`connectivity-results-${propertyId}`);
  const btn = document.getElementById(`connectivity-btn-${propertyId}`);
  
  if (!btn || !resultsDiv) {
    console.error('❌ Button or results div not found');
    return;
  }
  
  // Get coordinates from window.currentPropertyLocation (set by showPropertyDetails)
  if (!window.currentPropertyLocation || !window.currentPropertyLocation.lat || !window.currentPropertyLocation.lng) {
    console.error('❌ No property coordinates available');
    console.error('❌ window.currentPropertyLocation:', window.currentPropertyLocation);
    resultsDiv.innerHTML = '<p style="color:#f44336;font-size:13px;">Property coordinates not available.</p>';
    resultsDiv.style.display = 'block';
    return;
  }
  
  const lat = window.currentPropertyLocation.lat;
  const lng = window.currentPropertyLocation.lng;
  
  console.log('✅ Using coordinates:', lat, lng);
  
  // Clear previous connectivity routes and markers
  if (window.connectivityAnimations) {
    window.connectivityAnimations.forEach(interval => clearInterval(interval));
    window.connectivityAnimations = [];
  }
  if (window.connectivityMarkers) {
    window.connectivityMarkers.forEach(marker => marker.remove());
    window.connectivityMarkers = [];
  }
  
  btn.disabled = true;
  btn.innerHTML = '⏳ Finding routes...';
  
  // Show loading state in results
  resultsDiv.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:center;padding:20px;color:#666;">
      <div style="text-align:center;">
        <div style="font-size:24px;margin-bottom:8px;">🔍</div>
        <div style="font-size:13px;">Searching for connectivity options...</div>
      </div>
    </div>
  `;
  resultsDiv.style.display = 'block';
  
  try {
    // Define search types with VERY specific keywords to differentiate railway vs metro
    const searches = [
      { type: 'railway', keyword: 'indian railway station junction', color: '#FF4500', icon: '🚂', label: 'Railway Station', placeType: 'train_station' },
      { type: 'metro', keyword: 'hyderabad metro station', color: '#8B00FF', icon: '🚇', label: 'Metro Station', placeType: 'subway_station' },
      { type: 'airport', keyword: 'international airport', color: '#0080FF', icon: '✈️', label: 'Airport', placeType: 'airport' }
    ];
    
    console.log('🔍 Searching for connectivity options...');
    
    // Fetch all places in parallel for better performance
    const results = await Promise.all(
      searches.map(async (search) => {
        try {
          const url = `${window.API_BASE_URL}/api/nearby-places?lat=${lat}&lng=${lng}&keyword=${encodeURIComponent(search.keyword)}&radius=50000&place_type=${search.placeType}`;
          console.log(`🔍 Fetching ${search.type}:`, url);
          
          const response = await fetch(url);
          
          if (!response.ok) {
            console.error(`❌ ${search.type} HTTP error:`, response.status, response.statusText);
            return null;
          }
          
          const data = await response.json();
          console.log(`✅ ${search.type} response:`, data);
          
          if (data.success && data.places && data.places.length > 0) {
            // Calculate distance for ALL returned places
            const placesWithDistance = data.places.map(place => ({
              ...place,
              distance: calculateDistance(lat, lng, place.lat, place.lng)
            }));
            
            // Sort by distance and pick the nearest one
            placesWithDistance.sort((a, b) => a.distance - b.distance);
            const nearest = placesWithDistance[0];
            
            console.log(`✅ ${search.type} - Found ${placesWithDistance.length} options`);
            console.log(`   🎯 NEAREST: ${nearest.name} at ${nearest.distance.toFixed(2)} km`);
            console.log(`   📍 Property coords: (${lat}, ${lng})`);
            console.log(`   📍 ${nearest.name} coords: (${nearest.lat}, ${nearest.lng})`);
            if (placesWithDistance.length > 1) {
              console.log(`   Other options:`);
              placesWithDistance.slice(1, 5).forEach((p, i) => {
                console.log(`      ${i+2}. ${p.name} - ${p.distance.toFixed(2)} km`);
              });
            }
            
            return {
              ...search,
              place: nearest,
              distance: nearest.distance
            };
          } else {
            console.warn(`⚠️ ${search.type} no results:`, data);
          }
        } catch (error) {
          console.error(`❌ Error searching for ${search.type}:`, error);
        }
        return null;
      })
    );
    
    console.log('📊 All results:', results);
    
    // Filter out nulls
    const validResults = results.filter(r => r !== null);
    console.log('✅ Valid results:', validResults);
    
    if (validResults.length === 0) {
      resultsDiv.innerHTML = '<p style="color:#999;font-size:13px;">No connectivity options found nearby.</p>';
      resultsDiv.style.display = 'block';
      btn.disabled = false;
      btn.innerHTML = '🚉 Show Connectivity';
      return;
    }
    
    // Display results with enhanced styling
    let html = '<div style="display:flex;flex-direction:column;gap:12px;">';
    validResults.forEach(result => {
      html += `
        <div style="background:linear-gradient(135deg, white, ${result.color}08);border:2px solid ${result.color};border-radius:10px;padding:14px;box-shadow:0 2px 8px rgba(0,0,0,0.1);transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="font-size:24px;">${result.icon}</span>
            <strong style="color:${result.color};font-size:14px;text-transform:uppercase;letter-spacing:0.5px;">${result.label}</strong>
          </div>
          <div style="font-size:13px;color:#333;margin-bottom:6px;font-weight:500;">${result.place.name}</div>
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:12px;color:#666;">📍 ${result.distance.toFixed(2)} km away</span>
          </div>
        </div>
      `;
    });
    html += '</div>';
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    // Draw routes on map with animation
    await drawConnectivityRoutes(lat, lng, validResults);
    
    btn.disabled = false;
    btn.innerHTML = '✓ Routes Shown';
    btn.style.background = 'linear-gradient(135deg,#10B981,#059669)';
    
  } catch (error) {
    console.error('❌ Connectivity error:', error);
    resultsDiv.innerHTML = '<p style="color:#f44336;font-size:13px;">Failed to load connectivity data.</p>';
    resultsDiv.style.display = 'block';
    btn.disabled = false;
    btn.innerHTML = '🚉 Show Connectivity';
  }
}

// Calculate distance between two points (Haversine formula)
function calculateDistance(lat1, lng1, lat2, lng2) {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

// Draw connectivity routes on map with animation
async function drawConnectivityRoutes(originLat, originLng, results) {
  console.log('🎨 Drawing connectivity routes with animation...');
  
  // Clear existing connectivity routes
  results.forEach(result => {
    if (map.getLayer(`connectivity-route-${result.type}-outline`)) {
      map.removeLayer(`connectivity-route-${result.type}-outline`);
    }
    if (map.getLayer(`connectivity-route-${result.type}`)) {
      map.removeLayer(`connectivity-route-${result.type}`);
    }
    if (map.getSource(`connectivity-route-${result.type}`)) {
      map.removeSource(`connectivity-route-${result.type}`);
    }
  });
  
  // Fetch all routes in parallel for better performance
  const routePromises = results.map(async (result) => {
    try {
      const response = await fetch(
        `${window.API_BASE_URL}/api/directions?origin_lat=${originLat}&origin_lng=${originLng}&dest_place_id=${result.place.place_id}`
      );
      const data = await response.json();
      
      if (data.success && data.routes && data.routes.driving) {
        return {
          result,
          route: data.routes.driving,
          coordinates: decodePolyline(data.routes.driving.polyline)
        };
      }
    } catch (error) {
      console.error(`Failed to fetch ${result.type} route:`, error);
    }
    return null;
  });
  
  const routeData = (await Promise.all(routePromises)).filter(r => r !== null);
  
  // Draw all routes with enhanced styling
  routeData.forEach(({ result, route, coordinates }) => {
    // Add source
    map.addSource(`connectivity-route-${result.type}`, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: coordinates
        },
        properties: {
          type: result.type,
          name: result.place.name,
          distance: result.distance
        }
      }
    });
    
    // Add outline layer for better visibility (darker/thicker)
    map.addLayer({
      id: `connectivity-route-${result.type}-outline`,
      type: 'line',
      source: `connectivity-route-${result.type}`,
      paint: {
        'line-color': '#000000',
        'line-width': 5,
        'line-opacity': 0.25
      }
    });
    
    // Add main route layer - SOLID, BRIGHT, THINNER
    map.addLayer({
      id: `connectivity-route-${result.type}`,
      type: 'line',
      source: `connectivity-route-${result.type}`,
      paint: {
        'line-color': result.color,
        'line-width': 4,
        'line-opacity': 1.0  // Full opacity for maximum brightness
      }
    });
    
    console.log(`✅ Drew ${result.type} route with solid bright line`);
  });
  
  // Hide property pins for cleaner view
  if (map.getLayer('property-pins-layer')) {
    map.setLayoutProperty('property-pins-layer', 'visibility', 'none');
  }
  if (map.getLayer('property-pins-labels')) {
    map.setLayoutProperty('property-pins-labels', 'visibility', 'none');
  }
  
  // Add markers for origin and destinations
  results.forEach(result => {
    // Create a compact destination marker - MUCH SMALLER
    const el = document.createElement('div');
    el.className = 'connectivity-marker';
    el.style.cssText = `
      width: 28px;
      height: 28px;
      background: ${result.color};
      border: 2px solid white;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      animation: bounce 2s infinite;
    `;
    
    const iconSpan = document.createElement('span');
    iconSpan.innerHTML = result.icon;
    iconSpan.style.cssText = `
      font-size: 14px;
      transform: rotate(45deg);
      display: block;
    `;
    el.appendChild(iconSpan);
    
    const marker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
      .setLngLat([result.place.lng, result.place.lat])
      .setPopup(
        new maplibregl.Popup({ offset: 20, closeButton: false })
          .setHTML(`
            <div style="padding:8px;min-width:160px;">
              <strong style="color:${result.color};font-size:13px;display:flex;align-items:center;gap:6px;">
                ${result.icon} ${result.label}
              </strong>
              <div style="margin-top:4px;font-size:12px;font-weight:500;">${result.place.name}</div>
              <div style="margin-top:2px;font-size:11px;color:#666;">📍 ${result.distance.toFixed(2)} km away</div>
            </div>
          `)
      )
      .addTo(map);
    
    // Auto-show popup for better visibility
    marker.togglePopup();
    
    if (!window.connectivityMarkers) {
      window.connectivityMarkers = [];
    }
    window.connectivityMarkers.push(marker);
  });
  
  // Origin marker - MUCH SMALLER
  const originEl = document.createElement('div');
  originEl.className = 'connectivity-origin-marker';
  originEl.style.cssText = `
    width: 30px;
    height: 30px;
    background: linear-gradient(135deg, #10B981, #059669);
    border: 2px solid white;
    border-radius: 50% 50% 50% 0;
    transform: rotate(-45deg);
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse 2s infinite;
  `;
  
  const originIconSpan = document.createElement('span');
  originIconSpan.innerHTML = '🏠';
  originIconSpan.style.cssText = `
    font-size: 15px;
    transform: rotate(45deg);
    display: block;
  `;
  originEl.appendChild(originIconSpan);
  
  const originMarker = new maplibregl.Marker({ element: originEl, anchor: 'bottom' })
    .setLngLat([originLng, originLat])
    .setPopup(
      new maplibregl.Popup({ offset: 20, closeButton: false })
        .setHTML('<div style="padding:8px;"><strong style="font-size:13px;">🏠 Property Location</strong></div>')
    )
    .addTo(map);
  
  // Auto-show popup
  originMarker.togglePopup();
  
  if (!window.connectivityMarkers) {
    window.connectivityMarkers = [];
  }
  window.connectivityMarkers.push(originMarker);
  
  // Adjust map view to show all routes with smooth animation
  const allCoords = results.map(r => [r.place.lng, r.place.lat]);
  allCoords.push([originLng, originLat]);
  
  const bounds = allCoords.reduce((bounds, coord) => {
    return bounds.extend(coord);
  }, new maplibregl.LngLatBounds(allCoords[0], allCoords[0]));
  
  map.fitBounds(bounds, {
    padding: { top: 100, bottom: 100, left: 100, right: 450 },
    maxZoom: 13,
    duration: 1500 // Smooth animation
  });
}

document.getElementById('commute-close').addEventListener('click', function() {
  document.getElementById('commute-modal-overlay').style.display = 'none';
  clearRoutes();
});

// Office search with autocomplete
let searchTimeout;
document.getElementById('office-search-input').addEventListener('input', function(e) {
  const query = e.target.value.trim();
  
  clearTimeout(searchTimeout);
  
  if (query.length < 3) {
    document.getElementById('office-suggestions').innerHTML = '';
    return;
  }
  
  searchTimeout = setTimeout(() => {
    searchOffice(query);
  }, 300);
});

async function searchOffice(query) {
  try {
    const response = await fetch(`${window.API_BASE_URL}/api/search-place?query=${encodeURIComponent(query)}`);
    const data = await response.json();
    
    if (data.success && data.suggestions.length > 0) {
      displaySuggestions(data.suggestions);
    } else {
      document.getElementById('office-suggestions').innerHTML = '<div class="no-suggestions">No results found</div>';
    }
  } catch (error) {
    console.error('Error searching office:', error);
    document.getElementById('office-suggestions').innerHTML = '<div class="no-suggestions">Error searching</div>';
  }
}

function displaySuggestions(suggestions) {
  const suggestionsEl = document.getElementById('office-suggestions');
  
  suggestionsEl.innerHTML = suggestions.map(s => `
    <div class="suggestion-item" onclick="selectOffice('${s.place_id}', '${s.description.replace(/'/g, "\\'")}')">
      <div class="suggestion-main">${s.main_text}</div>
      <div class="suggestion-secondary">${s.secondary_text}</div>
    </div>
  `).join('');
}

window.selectOffice = async function(placeId, description) {
  console.log('🔍 Selecting office:', description, 'Place ID:', placeId);
  console.log('📍 Property location:', currentPropertyLocation);
  
  if (!currentPropertyLocation || !currentPropertyLocation.lat || !currentPropertyLocation.lng) {
    console.error('❌ No property location set!');
    alert('Error: Property location not available');
    return;
  }
  
  document.getElementById('office-suggestions').innerHTML = '';
  document.getElementById('office-search-input').value = description;
  
  // Store destination info
  window.currentDestination = { placeId, description };
  
  // Show loading
  const routesSection = document.getElementById('commute-routes-section');
  routesSection.style.display = 'block';
  document.getElementById('route-info-cards').innerHTML = '<div class="loading-routes">Calculating routes...</div>';
  
  try {
    const url = `${window.API_BASE_URL}/api/directions?origin_lat=${currentPropertyLocation.lat}&origin_lng=${currentPropertyLocation.lng}&dest_place_id=${placeId}`;
    console.log('🌐 Fetching directions from:', url);
    console.log('🌐 API_BASE_URL:', window.API_BASE_URL);
    
    const response = await fetch(url);
    console.log('📡 Response status:', response.status);
    
    const data = await response.json();
    console.log('📦 Response data:', data);
    
    if (data.success && data.routes) {
      console.log('✅ Routes received:', Object.keys(data.routes));
      window.currentRoutes = data.routes;
      
      // Store destination coordinates from the route
      if (data.routes.driving && data.routes.driving.end_address) {
        window.currentDestination.address = data.routes.driving.end_address;
      }
      
      displayRoutes(data.routes);
      drawRoute('driving'); // Show driving route by default
    } else {
      console.error('❌ No routes in response:', data);
      document.getElementById('route-info-cards').innerHTML = `<div class="error-routes">Could not calculate routes: ${data.error || 'Unknown error'}</div>`;
    }
  } catch (error) {
    console.error('❌ Error getting directions:', error);
    document.getElementById('route-info-cards').innerHTML = `<div class="error-routes">Error calculating routes: ${error.message}</div>`;
  }
};

function displayRoutes(routes) {
  const cardsHTML = [];
  
  if (routes.driving) {
    cardsHTML.push(`
      <div class="route-card" data-mode="driving" onclick="drawRoute('driving')" style="cursor: pointer;">
        <div class="route-card-icon">🚗</div>
        <div class="route-card-content">
          <div class="route-card-title">Car (with traffic)</div>
          <div class="route-card-stats">
            <span class="route-stat"><strong>${routes.driving.distance}</strong></span>
            <span class="route-stat"><strong>${routes.driving.duration_in_traffic}</strong></span>
          </div>
        </div>
      </div>
    `);
  }
  
  if (routes.transit) {
    const modes = routes.transit.transit_modes.join(', ') || 'Metro/Bus';
    cardsHTML.push(`
      <div class="route-card" data-mode="transit" onclick="drawRoute('transit')" style="cursor: pointer;">
        <div class="route-card-icon">🚇</div>
        <div class="route-card-content">
          <div class="route-card-title">Transit (${modes})</div>
          <div class="route-card-stats">
            <span class="route-stat"><strong>${routes.transit.distance}</strong></span>
            <span class="route-stat"><strong>${routes.transit.duration}</strong></span>
          </div>
        </div>
      </div>
    `);
  }
  
  if (routes.bus) {
    cardsHTML.push(`
      <div class="route-card" data-mode="bus" onclick="drawRoute('bus')" style="cursor: pointer;">
        <div class="route-card-icon">🚌</div>
        <div class="route-card-content">
          <div class="route-card-title">Bus</div>
          <div class="route-card-stats">
            <span class="route-stat"><strong>${routes.bus.distance}</strong></span>
            <span class="route-stat"><strong>${routes.bus.duration}</strong></span>
          </div>
        </div>
      </div>
    `);
  }
  
  document.getElementById('route-info-cards').innerHTML = cardsHTML.join('');
}

window.toggleRoute = function(mode) {
  // Update button states
  document.querySelectorAll('.route-toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  
  // Draw the selected route
  drawRoute(mode);
};

function drawRoute(mode) {
  console.log('🗺️ Drawing route for mode:', mode);
  console.log('🗺️ Current routes available:', Object.keys(window.currentRoutes || {}));
  console.log('🗺️ currentPropertyLocation:', window.currentPropertyLocation);
  
  // Clear existing route layers first
  clearRoutes();
  
  const routes = window.currentRoutes;
  if (!routes) {
    console.error('❌ No routes available');
    return;
  }
  
  const route = routes[mode];
  
  if (!route) {
    console.error('❌ No route found for mode:', mode);
    console.error('❌ Available routes:', Object.keys(routes));
    return;
  }
  
  if (!route.polyline) {
    console.error('❌ No polyline in route:', route);
    return;
  }
  
  console.log('📍 Polyline:', route.polyline.substring(0, 50) + '...');
  
  // Decode polyline
  const coordinates = decodePolyline(route.polyline);
  console.log('✅ Decoded coordinates:', coordinates.length, 'points');
  
  if (coordinates.length === 0) {
    console.error('❌ No coordinates decoded');
    return;
  }
  
  console.log('🎨 Adding route to map...');
  
  // Always add fresh source and layers (since we cleared them above)
  map.addSource('commute-route', {
    type: 'geojson',
    data: {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: coordinates
      }
    }
  });
  
  console.log('✅ Source added');
  
  // Add white outline first (bottom layer)
  map.addLayer({
    id: 'commute-route-outline',
    type: 'line',
    source: 'commute-route',
    paint: {
      'line-color': '#FFFFFF',
      'line-width': 8,
      'line-opacity': 0.5
    }
  });
  
  console.log('✅ Outline layer added');
  
  // Add dark orange route line on top
  map.addLayer({
    id: 'commute-route-line',
    type: 'line',
    source: 'commute-route',
    paint: {
      'line-color': '#0004ffff',
      'line-width': 6,
      'line-opacity': 0.9,
      'line-blur': 2
    }
  });
  
  console.log('✅ Route line layer added');
  
  // Add start and end markers using MapLibre Markers with inline styles
  const endCoord = coordinates[coordinates.length - 1];
  
  // Remove old markers if they exist
  if (window.commuteStartMarker) {
    window.commuteStartMarker.remove();
  }
  if (window.commuteEndMarker) {
    window.commuteEndMarker.remove();
  }
  
  // Check if we have property location
  if (!window.currentPropertyLocation) {
    console.error('❌ No currentPropertyLocation set');
    return;
  }
  
  // Create start marker (property)
  const startEl = document.createElement('div');
  startEl.style.cssText = `
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    border-radius: 50%;
    border: 3px solid white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
  `;
  startEl.innerHTML = '🏠';
  
  window.commuteStartMarker = new maplibregl.Marker({ 
    element: startEl,
    anchor: 'center'
  })
    .setLngLat([window.currentPropertyLocation.lng, window.currentPropertyLocation.lat])
    .addTo(map);
  
  // Create end marker (office)
  const endEl = document.createElement('div');
  endEl.style.cssText = `
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    border-radius: 50%;
    border: 3px solid white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    cursor: pointer;
  `;
  endEl.innerHTML = '🏢';
  
  window.commuteEndMarker = new maplibregl.Marker({ 
    element: endEl,
    anchor: 'center'
  })
    .setLngLat(endCoord)
    .addTo(map);
  
  console.log('✅ Route drawn on map with markers');
  
  // Fit map to show the route with proper padding
  // Account for properties panel on the right (320px width)
  const bounds = coordinates.reduce((bounds, coord) => {
    return bounds.extend(coord);
  }, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));
  
  map.fitBounds(bounds, { 
    padding: {
      top: 80,
      bottom: 80,
      left: 80,
      right: 400  // Extra padding on right for properties panel
    },
    duration: 1000
  });
  console.log('✅ Map fitted to route bounds');
}

function clearRoutes() {
  console.log('🧹 Clearing routes from map');
  
  // Clear commute routes
  if (map.getLayer('commute-route-outline')) {
    map.removeLayer('commute-route-outline');
  }
  if (map.getLayer('commute-route-line')) {
    map.removeLayer('commute-route-line');
  }
  if (map.getSource('commute-route')) {
    map.removeSource('commute-route');
  }
  
  // Clear connectivity routes and animations
  ['railway', 'metro', 'airport'].forEach(type => {
    if (map.getLayer(`connectivity-route-${type}-outline`)) {
      map.removeLayer(`connectivity-route-${type}-outline`);
    }
    if (map.getLayer(`connectivity-route-${type}`)) {
      map.removeLayer(`connectivity-route-${type}`);
    }
    if (map.getSource(`connectivity-route-${type}`)) {
      map.removeSource(`connectivity-route-${type}`);
    }
  });
  
  // Clear connectivity animations
  if (window.connectivityAnimations) {
    window.connectivityAnimations.forEach(interval => clearInterval(interval));
    window.connectivityAnimations = [];
  }
  
  // Clear connectivity markers
  if (window.connectivityMarkers) {
    window.connectivityMarkers.forEach(marker => marker.remove());
    window.connectivityMarkers = [];
  }
  
  // Restore property pins visibility
  if (map.getLayer('property-pins-layer')) {
    map.setLayoutProperty('property-pins-layer', 'visibility', 'visible');
  }
  if (map.getLayer('property-pins-labels')) {
    map.setLayoutProperty('property-pins-labels', 'visibility', 'visible');
  }
  
  // Remove marker layers
  if (map.getLayer('commute-markers-symbols')) {
    map.removeLayer('commute-markers-symbols');
  }
  if (map.getLayer('commute-markers-layer')) {
    map.removeLayer('commute-markers-layer');
  }
  if (map.getSource('commute-markers')) {
    map.removeSource('commute-markers');
  }
  
  // Remove markers
  if (window.commuteStartMarker) {
    window.commuteStartMarker.remove();
    window.commuteStartMarker = null;
  }
  if (window.commuteEndMarker) {
    window.commuteEndMarker.remove();
    window.commuteEndMarker = null;
  }
}

// Decode Google polyline format
function decodePolyline(encoded) {
  const coordinates = [];
  let index = 0, len = encoded.length;
  let lat = 0, lng = 0;
  
  while (index < len) {
    let b, shift = 0, result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
    lat += dlat;
    
    shift = 0;
    result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
    lng += dlng;
    
    coordinates.push([lng / 1e5, lat / 1e5]);
  }
  
  return coordinates;
}


// Commute calculator in property detail drawer
document.addEventListener('input', function(e) {
  if (e.target.classList.contains('office-search-input-detail')) {
    const input = e.target;
    const query = input.value.trim();
    const propId = input.id.replace('office-search-detail-', '');
    const suggestionsEl = document.getElementById(`office-suggestions-detail-${propId}`);
    
    if (query.length < 3) {
      suggestionsEl.innerHTML = '';
      return;
    }
    
    fetch(`${window.API_BASE_URL}/api/search-place?query=${encodeURIComponent(query)}`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.suggestions.length > 0) {
          suggestionsEl.innerHTML = data.suggestions.map(s => `
            <div class="suggestion-item" onclick="selectOfficeDetail('${propId}', '${s.place_id}', '${s.description.replace(/'/g, "\\'")}', this)">
              <div class="suggestion-main">${s.main_text}</div>
              <div class="suggestion-secondary">${s.secondary_text}</div>
            </div>
          `).join('');
        } else {
          suggestionsEl.innerHTML = '<div class="no-suggestions">No results found</div>';
        }
      })
      .catch(error => {
        console.error('Error searching:', error);
        suggestionsEl.innerHTML = '<div class="no-suggestions">Error searching</div>';
      });
  }
});

window.selectOfficeDetail = async function(propId, placeId, description, element) {
  const input = document.getElementById(`office-search-detail-${propId}`);
  const suggestionsEl = document.getElementById(`office-suggestions-detail-${propId}`);
  const routesEl = document.getElementById(`commute-routes-detail-${propId}`);
  const routeCardsEl = routesEl.querySelector('.route-cards-detail');
  
  const propLat = parseFloat(input.dataset.propLat);
  const propLng = parseFloat(input.dataset.propLng);
  const propName = input.dataset.propName;
  
  input.value = description;
  suggestionsEl.innerHTML = '';
  
  // Store for map drawing
  window.currentPropertyLocation = { lat: propLat, lng: propLng, name: propName };
  window.currentDestination = { placeId, description };
  
  // Show loading
  routesEl.style.display = 'block';
  routeCardsEl.innerHTML = '<div class="loading-routes">Calculating routes...</div>';
  
  try {
    const url = `${window.API_BASE_URL}/api/directions?origin_lat=${propLat}&origin_lng=${propLng}&dest_place_id=${placeId}`;
    const response = await fetch(url);
    const data = await response.json();
    
    if (data.success && data.routes) {
      window.currentRoutes = data.routes;
      
      const cardsHTML = [];
      
      if (data.routes.driving) {
        cardsHTML.push(`
          <div class="route-card-compact" onclick="drawRoute('driving')">
            <div class="route-icon">🚗</div>
            <div class="route-info">
              <div class="route-mode">Car</div>
              <div class="route-stats">${data.routes.driving.distance} • ${data.routes.driving.duration_in_traffic}</div>
            </div>
          </div>
        `);
      }
      
      if (data.routes.transit) {
        cardsHTML.push(`
          <div class="route-card-compact" onclick="drawRoute('transit')">
            <div class="route-icon">🚇</div>
            <div class="route-info">
              <div class="route-mode">Transit</div>
              <div class="route-stats">${data.routes.transit.distance} • ${data.routes.transit.duration}</div>
            </div>
          </div>
        `);
      }
      
      if (data.routes.bus) {
        cardsHTML.push(`
          <div class="route-card-compact" onclick="drawRoute('bus')">
            <div class="route-icon">🚌</div>
            <div class="route-info">
              <div class="route-mode">Bus</div>
              <div class="route-stats">${data.routes.bus.distance} • ${data.routes.bus.duration}</div>
            </div>
          </div>
        `);
      }
      
      routeCardsEl.innerHTML = cardsHTML.join('');
      drawRoute('driving');
    } else {
      routeCardsEl.innerHTML = '<div class="error-routes">Could not calculate routes</div>';
    }
  } catch (error) {
    console.error('Error:', error);
    routeCardsEl.innerHTML = '<div class="error-routes">Error calculating routes</div>';
  }
};
