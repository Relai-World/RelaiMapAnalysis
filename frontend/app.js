console.log("App.js Loaded - V 1.5 - Absolute Paths Maptiles");

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

// DEBUG: Check Lakes Metadata
async function checkLakes() {
  try {
    const p = new pmtiles.PMTiles("maptiles/lakes.pmtiles");
    const metadata = await p.getMetadata();
    console.log("=== LAKES METADATA ===");
    if (metadata && metadata.vector_layers) {
      console.log("LAYERS:", metadata.vector_layers);
    } else {
      console.log("Metadata:", metadata);
    }
  } catch (e) { console.error("Lakes Check Failed:", e); }
}
checkLakes();



const map = new maplibregl.Map({
  container: "map",
  style: 'https://tiles.openfreemap.org/styles/liberty',
  //style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  //style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',

  center: [78.38, 17.44],
  zoom: 11,
  minZoom: 4,
  maxZoom: 18
});

// 🚀 EARLY FETCH: Start getting data immediately while map initializes
const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const BACKEND_URL = isLocal ? "http://127.0.0.1:8000" : "https://west-hyderabad-intelliweb.onrender.com";
const insightsPromise = fetch(`${BACKEND_URL}/api/v1/insights`).then(res => res.json());

map.addControl(new maplibregl.NavigationControl());

let activeMarker = null;

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
  doc.text("WEST HYDERABAD INTELLIGENCE", 14, y);
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
  doc.text("Source: West Hyderabad Real Estate Intelligence Platform", 14, 285);
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
    maxzoom: 14
  });
  map.addLayer({
    id: "orr-layer",
    type: "line",
    source: "orr-source",
    "source-layer": "orr",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#000000ff", "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.5, 18, 6], "line-blur": 1, "line-opacity": 0 } // Ghost state
  });

  // 3. Highways
  map.addSource("highways-source", {
    type: "vector", url: `pmtiles://${BASE_TILES_URL}/highways.pmtiles`,
    minzoom: 0,
    maxzoom: 14
  });
  map.addLayer({
    id: "highways-layer",
    type: "line",
    source: "highways-source",
    "source-layer": "highways",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#64008fff", "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.2, 18, 4.8], "line-blur": 1, "line-opacity": 0 } // Ghost state
  });

  // 4. Metro
  map.addSource("metro-source", {
    type: "vector", url: `pmtiles://${BASE_TILES_URL}/metro.pmtiles`,
    minzoom: 0,
    maxzoom: 14
  });
  map.addLayer({
    id: "metro-layer",
    type: "line",
    source: "metro-source",
    "source-layer": "metro",
    layout: { visibility: "visible", "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#f00b0bff", "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.2, 18, 4.8], "line-blur": 1, "line-opacity": 0 } // Ghost state
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
      "line-opacity": 0 // Ghost state
    }
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
      "line-opacity": 0 // Ghost state
    }
  });

  // 1. Lakes (Moved to end)
  map.addSource("lakes-source", { type: "vector", url: `pmtiles://${BASE_TILES_URL}/lakes.pmtiles` });
  map.addLayer({
    id: "lakes-layer",
    type: "fill",
    source: "lakes-source",
    "source-layer": "lakes",
    layout: { visibility: "visible" },
    paint: {
      "fill-color": "#0077ff",
      "fill-opacity": 0
    }
  });

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
      "line-opacity": 0 // Ghost state
    }
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
    }
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
      "circle-opacity": 0, // Ghost state
      "circle-stroke-opacity": 0
    }
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
      "text-opacity": 0 // Ghost state
    }
  });



  // MAP INIT (USING LOCALLY HOSTED PMTILES) - removed to avoid conflict

  try {
    const data = await insightsPromise;
    const searchInput = document.getElementById("location-search");
    const searchResults = document.getElementById("search-results");

    if (searchInput && searchResults) {
      searchInput.addEventListener("focus", () => {
        // We don't necessarily hide the card on focus if a location is already selected,
        // but we should ensure the UI state is consistent.
      });

      // Input Event
      searchInput.addEventListener("input", (e) => {
        const val = e.target.value.toLowerCase();
        searchResults.innerHTML = "";

        const card = document.getElementById("intel-card");
        const emptyState = document.getElementById("empty-state");

        if (val.length < 1) {
          searchResults.style.display = "none";
          if (card.style.display === "none") {
            if (emptyState) emptyState.style.display = "flex";
          }
          return;
        }

        // Hide empty state if results appear
        if (emptyState) emptyState.style.display = "none";

        // Filter: Strictly starts with the search term
        const matches = data
          .filter(d => d.location.toLowerCase().startsWith(val))
          .sort((a, b) => a.location.localeCompare(b.location));

        if (matches.length > 0) {
          matches.slice(0, 8).forEach(loc => { // Limit to top 8 suggestions
            const div = document.createElement("div");
            div.className = "search-result-item";
            div.textContent = loc.location;
            // Highlight exact match if typed fully
            if (loc.location.toLowerCase() === val) {
              div.style.background = "rgba(59, 130, 246, 0.2)";
            }
            div.onclick = () => {
              searchInput.value = loc.location;
              handleLocationSelect(loc);
              searchResults.style.display = "none";
            };
            searchResults.appendChild(div);
          });
          searchResults.style.display = "block";
        } else {
          // Show "No Result Found"
          const div = document.createElement("div");
          div.className = "search-result-item";
          div.style.cursor = "default";
          div.style.fontStyle = "italic";
          div.style.color = "#94a3b8";
          div.textContent = "No result found";
          searchResults.appendChild(div);
          searchResults.style.display = "block";
        }
      });

      // Enter Key Navigation
      searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          const val = searchInput.value.toLowerCase();

          // Find exact match or first 'starts with' match
          const bestMatch = data.find(d => d.location.toLowerCase() === val) ||
            data.find(d => d.location.toLowerCase().startsWith(val));

          if (bestMatch) {
            searchInput.value = bestMatch.location;
            handleLocationSelect(bestMatch);
            searchResults.style.display = "none";
            searchInput.blur();
          } else {
            // Keep "No result found" visible if already there, or ensure it shows
            if (searchResults.style.display === "none") {
              // Force trigger input event logic to show "no result" if not open
              searchInput.dispatchEvent(new Event('input'));
            }
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

    // GLOW RING (renders behind the dot for depth)
    map.addLayer({
      id: "location-glow",
      type: "circle",
      source: "locations",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 10, 15, 18],
        "circle-color": [
          "interpolate", ["linear"], ["get", "investment_score"],
          0.0, "#F43F5E",
          0.5, "#EAB308",
          0.7, "#10B981",
          1.0, "#14B8A6"
        ],
        "circle-opacity": 0.12,
        "circle-stroke-width": 0,
        "circle-blur": 1
      }
    });

    // GOLD CORE DOT — uniform gold coin style
    map.addLayer({
      id: "location-core",
      type: "circle",
      source: "locations",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 6, 14, 10],
        "circle-color": "#D4AF37",
        "circle-stroke-color": "#1A2744",
        "circle-stroke-width": 2
      }
    });
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
  };

  document.querySelectorAll(".layer-toggle input").forEach(cb => {
    cb.onchange = e => {
      const id = e.target.dataset.layer;
      const targetOpacity = e.target.checked ? (opacities[id] || 1) : 0;

      if (map.getLayer(id)) {
        const type = map.getLayer(id).type;
        if (type === "fill") map.setPaintProperty(id, "fill-opacity", targetOpacity);
        if (type === "line") map.setPaintProperty(id, "line-opacity", targetOpacity);
        if (type === "symbol") map.setPaintProperty(id, "icon-opacity", targetOpacity);
        if (type === "circle") {
          map.setPaintProperty(id, "circle-opacity", targetOpacity);
          map.setPaintProperty(id, "circle-stroke-opacity", targetOpacity);
        }
        if (type === "raster") map.setPaintProperty(id, "raster-opacity", targetOpacity);
        if (type === "heatmap") map.setPaintProperty(id, "heatmap-opacity", targetOpacity);
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
                <h2 class="serif" style="margin: 0 0 4px 0; font-size: 1.4rem; color: var(--text-100);">Flood Intelligence</h2>
                <p style="color: var(--text-400); font-size: 10px; margin: 0; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700;">18 September 2025 Reports</p>
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

      // Distinct teal fill — clearly differentiates the active locality
      map.addLayer({
        id: 'location-boundary-fill',
        type: 'fill',
        source: 'location-boundary',
        paint: {
          'fill-color': '#14B8A6',
          'fill-opacity': 0.2
        }
      }, 'location-core');

      // Bold boundary stroke
      map.addLayer({
        id: 'location-boundary-line',
        type: 'line',
        source: 'location-boundary',
        paint: {
          'line-color': '#0D9488',
          'line-width': 3,
          'line-opacity': 1
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
    // START CLEANUP: Remove previous amenities if they exist
    clearAmenities();
    // END CLEANUP

    const card = document.getElementById("intel-card");
    const emptyState = document.getElementById("empty-state");

    if (emptyState) emptyState.style.display = "none";
    card.style.display = "flex";

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

    const sentimentScore = Math.min(Math.max((p.avg_sentiment + 0.5) * 100, 0), 100).toFixed(0);
    const growthVal = Math.min((p.growth_score * 10), 10).toFixed(1);
    const investVal = Math.min((p.investment_score * 10), 10).toFixed(1);

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
          <div class="location-hero-tag">📍 Elite Location</div>
          <div class="location-hero-name">${p.location}</div>
          <div class="location-hero-sub">Investment Score: ${investVal} / 10</div>
        </div>
      </div>

      <!-- METRICS (3 col) -->
      <div class="metrics">
        <div class="metric-box ${p.avg_sentiment >= 0 ? 'positive' : 'negative'}">
          <span>Sentiment</span>
          <strong>${sentimentScore}%</strong>
        </div>
        <div class="metric-box ${p.growth_score >= 0.6 ? 'positive' : 'neutral'}">
          <span>Growth</span>
          <strong>${growthVal}/10</strong>
        </div>
        <div class="metric-box ${p.investment_score >= 0.7 ? 'positive' : 'neutral'}">
          <span>Invest</span>
          <strong>${investVal}/10</strong>
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
          <button class="amenity-btn" data-amenity="metro_stations">
            <span class="btn-icon">🚇</span>
            <span class="btn-label">Metro</span>
          </button>
        </div>
        <div style="margin-top:8px; display:flex; justify-content:flex-end;">
          <button id="clear-amenities-btn" class="clear-btn" style="display:none;">✕ Clear</button>
        </div>
      </div>

      <!-- PRICE CHART -->
      <div class="chart-section">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
          <h4 class="section-label">Price Trend</h4>
          <span id="cagr-stat" style="font-size:11px; font-weight:700; color:var(--green); font-family:'Outfit',sans-serif;">Computing…</span>
        </div>
        <div class="chart-container">
          <canvas id="priceChart"></canvas>
        </div>
      </div>

      <button id="download-report">⬇ Download Intel Report</button>
    `;

    document.getElementById("download-report").onclick = () => generateReport(p);

    // FETCH AND DISPLAY PROPERTY COSTS DYNAMICALLY
    fetchPropertyCosts(p.location);

    // DRAW THE PRICE CHART
    drawPriceChart(p.location_id);

    if (activeMarker) activeMarker.remove();
    const markerEl = document.createElement('div');
    markerEl.className = 'active-location-marker';
    activeMarker = new maplibregl.Marker({ element: markerEl })
      .setLngLat([p.longitude, p.latitude])
      .addTo(map);
  }

  map.on("click", "location-core", async e => {
    const p = e.features[0].properties;
    handleLocationSelect(p);
  });

  map.on('mouseenter', 'location-core', () => {
    map.getCanvas().style.cursor = 'pointer';
  });
  map.on('mouseleave', 'location-core', () => {
    map.getCanvas().style.cursor = '';
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



  // CHART.JS HELPER
  function drawPriceChart(locationId) {
    fetch(`${BACKEND_URL}/api/v1/location/${locationId}/trends`)
      .then(res => res.json())
      .then(data => {
        // Check if data is valid array
        if (!Array.isArray(data) || data.length === 0) {
          console.warn('No chart data available');
          document.getElementById('cagr-stat').style.display = 'none';
          return;
        }

        // Calculate CAGR: ((EndValue / StartValue) ^ (1 / Years)) - 1
        if (data.length >= 2) {
          const startPrice = data[0].price;
          const endPrice = data[data.length - 1].price;
          const years = data[data.length - 1].year - data[0].year;
          const cagr = (Math.pow(endPrice / startPrice, 1 / years) - 1) * 100;
          document.getElementById('cagr-stat').innerText = `${cagr.toFixed(1)}% CAGR`;
        } else {
          document.getElementById('cagr-stat').style.display = 'none';
        }

        const ctx = document.getElementById('priceChart').getContext('2d');

        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(212, 175, 55, 0.35)');
        gradient.addColorStop(1, 'rgba(212, 175, 55, 0)');

        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.map(d => d.year),
            datasets: [{
              label: 'Avg Price (₹/sqft)',
              data: data.map(d => d.price),
              borderColor: '#D4AF37',
              borderWidth: 2.5,
              fill: true,
              backgroundColor: gradient,
              tension: 0.45,
              pointRadius: 4,
              pointBackgroundColor: '#D4AF37',
              pointBorderColor: '#060A18',
              pointBorderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }, tooltip: {
                backgroundColor: 'rgba(9,14,31,0.95)',
                borderColor: 'rgba(212,175,55,0.3)',
                borderWidth: 1,
                titleColor: '#D4AF37',
                bodyColor: '#F1F5F9',
                titleFont: { family: 'Outfit', weight: '700' },
                bodyFont: { family: 'Outfit' },
                padding: 10
              }
            },
            scales: {
              x: { grid: { display: false }, ticks: { color: '#4A5F7A', font: { family: 'Outfit', size: 10 } } },
              y: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#4A5F7A', font: { family: 'Outfit', size: 10 }, callback: (v) => '₹' + v / 1000 + 'k' }
              }
            }
          }
        });
      })
      .catch(err => console.error("Chart Fetch Error:", err));
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

    fetch(`${BACKEND_URL}/api/v1/location-costs/${encodeURIComponent(locationName)}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
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
        currentCostData = data;

        // NEW: Update the Investment Fact Placeholder text immediately
        const invFactSpan = document.getElementById("invest-fact-price");
        if (invFactSpan) {
          invFactSpan.innerText = ` (~₹${data.avgSqft.toLocaleString()}/sqft)`;
          invFactSpan.style.opacity = 1;
        }

        // Render the property costs section
        // Render the property costs section
        container.innerHTML = `
          <div style="margin: 12px 12px 0; padding-top:12px; border-top:1px solid var(--border);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <span style="font-size:9px; font-weight:700; text-transform:uppercase; letter-spacing:2.5px; color:var(--navy); font-family:'Outfit',sans-serif;">&#128176; Property Costs</span>
              <span style="font-size:9px; color:var(--t3); background:var(--bg-elevated); padding:3px 9px; border-radius:6px; border:1px solid var(--border); font-family:'Outfit',sans-serif; font-weight:600;">${data.count} Props</span>
            </div>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-bottom:7px;">
              <div style="background:var(--bg-card); padding:12px; border-radius:10px; border:1px solid var(--border); border-top:2px solid var(--gold-mid); box-shadow:0 1px 4px rgba(26,26,46,0.05);">
                <div style="font-size:8px; color:var(--t4); margin-bottom:4px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Avg Base</div>
                <div style="font-size:1.15rem; font-weight:800; color:var(--gold); font-family:'Outfit',sans-serif; letter-spacing:-0.3px;">&#8377;${data.avgBase} Cr</div>
              </div>
              <div style="background:var(--bg-card); padding:12px; border-radius:10px; border:1px solid var(--border); border-top:2px solid var(--teal); box-shadow:0 1px 4px rgba(26,26,46,0.05);">
                <div style="font-size:8px; color:var(--t4); margin-bottom:4px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Avg / SqFt</div>
                <div style="font-size:1.15rem; font-weight:800; color:var(--teal); font-family:'Outfit',sans-serif; letter-spacing:-0.3px;">&#8377;${data.avgSqft.toLocaleString()}</div>
              </div>
            </div>
            
            <div style="padding:10px 12px; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; margin-bottom:6px; box-shadow:0 1px 4px rgba(26,26,46,0.04);">
              <div style="font-size:8px; color:var(--t4); margin-bottom:6px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Base Price Range</div>
              <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">&#8377;${data.minBase} Cr</span>
                <div style="flex:1; height:3px; background:var(--border); border-radius:2px; position:relative;">
                  <div style="position:absolute; inset:0; background:linear-gradient(90deg, var(--gold), var(--gold-bright)); border-radius:2px;"></div>
                </div>
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">&#8377;${data.maxBase} Cr</span>
              </div>
            </div>
            <div style="padding:10px 12px; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; box-shadow:0 1px 4px rgba(26,26,46,0.04);">
              <div style="font-size:8px; color:var(--t4); margin-bottom:6px; text-transform:uppercase; font-weight:700; letter-spacing:1px; font-family:'Outfit',sans-serif;">Price / SqFt Range</div>
              <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">&#8377;${data.minSqft.toLocaleString()}</span>
                <div style="flex:1; height:3px; background:var(--border); border-radius:2px; position:relative;">
                  <div style="position:absolute; inset:0; background:linear-gradient(90deg, var(--teal), #0A8A8E); border-radius:2px;"></div>
                </div>
                <span style="font-size:11px; font-weight:600; color:var(--t2); font-family:'Outfit',sans-serif;">&#8377;${data.maxSqft.toLocaleString()}</span>
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

  // ===============================
  // AMENITY DISPLAY FUNCTIONS
  // ===============================
  // Amenities state is now global (see top of file)

  function displayAmenitiesOnMap(locationId, amenityType) {
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

    // Fetch amenity data
    fetch(`${BACKEND_URL}/api/v1/location/${locationId}/amenities/${amenityType}`)
      .then(res => res.json())
      .then(data => {
        if (data.error || !data.amenities || data.amenities.length === 0) {
          alert(`No ${amenityType} found within 5km radius`);
          resetAmenityButtons(amenityType);
          return;
        }

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

        // Add source and layer with native MapLibre clustering enabled
        map.addSource('amenity-data', {
          type: 'geojson',
          data: geojson,
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 50
        });

        // 1. Add thick cluster circles
        map.addLayer({
          id: 'amenity-clusters',
          type: 'circle',
          source: 'amenity-data',
          filter: ['has', 'point_count'],
          paint: {
            // Colors: Hydrology style
            'circle-color': ['step', ['get', 'point_count'], '#A7C7E7', 5, '#4F8FBF', 15, '#1F5A8A'],
            'circle-radius': ['step', ['get', 'point_count'], 18, 5, 22, 15, 26],
            'circle-stroke-width': 3,
            'circle-stroke-color': '#ffffff'
          }
        });

        // 2. Add text count labels inside the clusters
        map.addLayer({
          id: 'amenity-cluster-counts',
          type: 'symbol',
          source: 'amenity-data',
          filter: ['has', 'point_count'],
          layout: {
            'text-field': '{point_count_abbreviated}',
            'text-size': 12
          },
          paint: {
            'text-color': '#ffffff'
          }
        });

        // Add pin markers using custom images
        const customIconId = `icon-${amenityType}`;
        const fallbackIcon = 'pin-gray';

        map.addLayer({
          id: 'amenity-markers',
          type: 'symbol',
          source: 'amenity-data',
          filter: ['!', ['has', 'point_count']], // ONLY show images for unclustered points
          layout: {
            'icon-image': map.hasImage(customIconId) ? customIconId : fallbackIcon,
            'icon-size': map.hasImage(customIconId) ? 0.04 : 0.55,  // Scaled down custom PNGs
            'icon-anchor': 'bottom',
            'icon-allow-overlap': true,
            'icon-ignore-placement': true
          },
          paint: {
            'icon-color': '#000000' // Ensure it renders dark if it's an sdf icon, otherwise does nothing
          }
        });

        currentAmenityLayer = 'amenity-markers';

        // Add click handler for clusters to zoom in
        map.on('click', 'amenity-clusters', (e) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ['amenity-clusters'] });
          const clusterId = features[0].properties.cluster_id;
          map.getSource('amenity-data').getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            map.flyTo({
              center: features[0].geometry.coordinates,
              zoom: zoom + 0.5,
              speed: 1.2,
              curve: 1.4,
              essential: true
            });
          });
        });

        // Change cursor on hover for clusters
        map.on('mouseenter', 'amenity-clusters', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'amenity-clusters', () => map.getCanvas().style.cursor = '');




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

        if (listCard && listContent && listTitle) {
          // Update Title
          const typeName = amenityType.charAt(0).toUpperCase() + amenityType.slice(1);
          listTitle.textContent = `Nearby ${typeName} (${data.total_count})`;

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
                <div class="amenity-name" style="font-size:0.9rem; font-weight:500;">${amenity.name}</div>
                <div style="display:flex; gap:6px; margin-top:8px;">
                  <span style="background:#E6F4EA; color:#166534; padding:3px 8px; border-radius:12px; font-size:10px; font-weight:600; border:1px solid #16653430;">📍 ${amenity.distance_km} km</span>
                  <span style="background:#F1F5F9; color:#334155; padding:3px 8px; border-radius:12px; font-size:10px; font-weight:600; text-transform:uppercase; border:1px solid #33415530;">${colorLabel}</span>
                </div>
              </div>
            `;

            // Click to Fly
            item.onclick = () => {
              map.flyTo({
                center: [amenity.longitude, amenity.latitude],
                zoom: 15,
                pitch: 45,
                essential: true
              });

              // Trigger Popup (Simulate)
              if (currentPopup) currentPopup.remove();
              currentPopup = new maplibregl.Popup({ closeButton: true, closeOnClick: true, maxWidth: '240px' })
                .setLngLat([amenity.longitude, amenity.latitude])
                .setHTML(`
                  <div class="popup-container" style="padding:16px;">
                    <div class="popup-title serif" style="font-size:16px; margin-bottom:8px;">${amenity.name}</div>
                    <div style="display:flex; gap:6px; flex-wrap:wrap;">
                      <span style="background:#E6F4EA; color:#166534; padding:4px 8px; border-radius:12px; font-size:10px; font-weight:600; border:1px solid #16653430;">📍 ${amenity.distance_km} km</span>
                      <span style="background:#F1F5F9; color:#334155; padding:4px 8px; border-radius:12px; font-size:10px; font-weight:600; text-transform:uppercase; border:1px solid #33415530;">${colorLabel}</span>
                    </div>
                  </div>
                `)
                .addTo(map);
            };

            listContent.appendChild(item);
          });

          // Show Card
          listCard.style.display = 'flex';
        }

      })
      .catch(err => {
        console.error('Amenity fetch error:', err);
        alert('Failed to load amenities. Please try again.');
        resetAmenityButtons(amenityType);
      });
  }

  function clearAmenities() {
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
        const icons = { hospitals: '🏥', schools: '🏫', malls: '🏪', restaurants: '🍽️', banks: '🏦', parks: '🏞️', metro_stations: '🚇' };
        const labels = { hospitals: 'Hospitals', schools: 'Schools', malls: 'Malls', restaurants: 'Food', banks: 'Banks', parks: 'Parks', metro_stations: 'Metro' };
        btn.innerHTML = `<span class="btn-icon">${icons[type] || '📍'}</span><span class="btn-label">${labels[type] || type}</span>`;
      });
    }
  }

  function resetAmenityButtons(activeType = null, count = null) {
    const amenityIcons = {
      hospitals: '🏥',
      schools: '🏫',
      malls: '🏪',
      restaurants: '🍽️',
      banks: '🏦',
      parks: '🏞️',
      metro_stations: '🚇'
    };

    const buttons = document.querySelectorAll('.amenity-btn');
    buttons.forEach(btn => {
      const type = btn.dataset.amenity;
      const icon = amenityIcons[type] || '📍';

      if (type === activeType && count !== null) {
        btn.innerHTML = `${icon} ${type.charAt(0).toUpperCase() + type.slice(1)} (${count})`;
        btn.style.opacity = '1';
        btn.style.transform = 'scale(1.05)';
      } else {
        btn.innerHTML = `${icon} ${type.charAt(0).toUpperCase() + type.slice(1)}`;
        btn.style.opacity = type === activeType ? '1' : '0.7';
        btn.style.transform = 'scale(1)';
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
      if (currentLocationId) {
        displayAmenitiesOnMap(currentLocationId, amenityType);
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
      const feature = features[0];
      const props = feature.properties;
      const card = document.getElementById("intel-card");

      card.style.display = "flex";

      let insightHtml = "";
      if (feature.layer.id === 'rainfall-layer') {
        insightHtml = `
          <div style="padding: 18px;">
            <p style="color: var(--text-400); font-size: 10px; text-transform: uppercase; margin: 0 0 8px 0; letter-spacing: 1.5px; font-weight: 700;">18 September 2025 &nbsp;·&nbsp; Rainfall</p>
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

            <div style="margin-top: 16px; padding: 12px; background: rgba(239, 68, 68, 0.07); border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.18);">
              <p style="margin: 0; font-size: 11px; color: #F87171; line-height: 1.5; font-weight: 500;">Historical area of concern. Vigilance advised during heavy rains.</p>
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

