console.log("App.js Loaded - V 1.5 - Absolute Paths Maptiles");

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

// DEBUG: Check ORR Metadata
async function checkORR() {
  try {
    const p = new pmtiles.PMTiles("maptiles/orr.pmtiles");
    const metadata = await p.getMetadata();
    console.log("=== ORR METADATA ===");
    if (metadata && metadata.vector_layers) {
      console.log("LAYERS:", metadata.vector_layers);
    } else {
      console.log("Metadata:", metadata);
    }
  } catch (e) { console.error("ORR Check Failed:", e); }
}
checkORR();



const map = new maplibregl.Map({
  container: "map",
  style: {
    "version": 8,
    "sources": {
      "osm": {
        "type": "raster",
        "tiles": ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
        "tileSize": 256,
        "attribution": "&copy; OpenStreetMap Contributors"
      }
    },
    "layers": [
      {
        "id": "osm",
        "type": "raster",
        "source": "osm"
      }
    ]
  },
  center: [78.38, 17.44],
  zoom: 11,
  minZoom: 4,
  maxZoom: 18
});

map.addControl(new maplibregl.NavigationControl());

let activeMarker = null;

/* ===============================
   TEXT HELPERS (SCALE-ALIGNED)
=============================== */
function sentimentText(v) {
  if (v >= 0.1) return "Positive";
  if (v <= -0.3) return "Negative";
  return "Neutral";
}

function growthText(v) {
  if (v >= 0.16) return "High";
  if (v >= 0.13) return "Medium";
  return "Low";
}

function investmentText(v) {
  if (v >= 0.22) return "Excellent";
  if (v >= 0.19) return "Good";
  return "Average";
}

/* ===============================
   UI – LAYERS ONLY
=============================== */
const layersBtn = document.getElementById("layers-btn");
const layersCard = document.getElementById("layers-card");
const closeLayers = document.getElementById("close-layers");

if (layersBtn && layersCard && closeLayers) {
  layersBtn.onclick = () => layersCard.style.display = "block";
  closeLayers.onclick = () => layersCard.style.display = "none";
}

/* ===============================
   PDF REPORT GENERATOR
=============================== */
function generateReport(p) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  doc.text("West Hyderabad – Real Estate Report", 14, 20);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(12);
  doc.text(`Location: ${p.location}`, 14, 36);
  doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 14, 46);

  doc.line(14, 52, 196, 52);

  doc.text("Insights:", 14, 66);
  doc.text(`• Market Sentiment: ${sentimentText(p.avg_sentiment)}`, 18, 78);
  doc.text(`• Growth Outlook: ${growthText(p.growth_score)}`, 18, 90);
  doc.text(`• Investment Score: ${investmentText(p.investment_score)}`, 18, 102);

  doc.save(`${p.location}_Real_Estate_Report.pdf`);
}

/* ===============================
   MAP LOAD
=============================== */
map.on("load", async () => {

  /* =====================================================
     📍 BASE TILE URL LOGIC
  ===================================================== */
  // If localhost, use simple relative path. If GitHub, use full absolute path to avoid lookup errors.
  const isLocalMap = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const BASE_TILES_URL = isLocalMap
    ? "maptiles"
    : "https://harjeet1309.github.io/west-hyderabad-intelliweb/frontend/maptiles";

  /* =====================================================
     🏫 SCHOOLS
  ===================================================== */
  map.loadImage(
    "./assets/schools.png",
    (error, image) => {
      if (!error && !map.hasImage("school-icon")) {
        map.addImage("school-icon", image);
      }

      map.addSource("schools-source", {
        type: "vector",
        url: `pmtiles://${BASE_TILES_URL}/schools.pmtiles`
      });

      map.addLayer({
        id: "schools-layer",
        type: "circle",
        source: "schools-source",
        "source-layer": "schools",
        layout: {
          visibility: "none"
        },
        paint: {
          "circle-radius": 6,
          "circle-color": "#FFD700", // Gold
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff"
        }
      });
    }
  );

  /* =====================================================
     🛣️ HIGHWAYS
  ===================================================== */
  map.addSource("highways-source", {
    type: "vector",
    url: `pmtiles://${BASE_TILES_URL}/highways.pmtiles`
  });

  map.addLayer({
    id: "highways-layer",
    type: "line",
    source: "highways-source",
    "source-layer": "highways",
    layout: {
      visibility: "none",
      "line-join": "round",
      "line-cap": "round"
    },
    paint: {
      "line-color": "#FFA500", // Orange
      "line-width": 3
    }
  });

  /* =====================================================
     🚇 METRO
  ===================================================== */
  map.addSource("metro-source", {
    type: "vector",
    url: `pmtiles://${BASE_TILES_URL}/metro.pmtiles` // Fixed filename
  });

  map.addLayer({
    id: "metro-layer",
    type: "line",
    source: "metro-source",
    "source-layer": "metro",
    layout: {
      visibility: "none",
      "line-join": "round",
      "line-cap": "round"
    },
    paint: {
      "line-color": "#FF0000", // Red
      "line-width": 4
    }
  });

  /* =====================================================
     🛣️ ORR
  ===================================================== */
  map.addSource("orr-source", {
    type: "vector",
    url: `pmtiles://${BASE_TILES_URL}/orr.pmtiles`
  });

  map.addLayer({
    id: "orr-layer",
    type: "line",
    source: "orr-source",
    "source-layer": "orr",
    layout: {
      visibility: "none",
      "line-join": "round",
      "line-cap": "round"
    },
    paint: {
      "line-color": "#0000FF", // Blue
      "line-width": 5
    }
  });

  /* =====================================================
     🌊 LAKES
  ===================================================== */
  map.addSource("lakes-source", {
    type: "vector",
    url: `pmtiles://${BASE_TILES_URL}/lakes.pmtiles`
  });

  map.addLayer({
    id: "lakes-layer",
    type: "fill",
    source: "lakes-source",
    "source-layer": "lakes",
    layout: { visibility: "none" },
    paint: {
      "fill-color": "#0077BE", // Blue
      "fill-opacity": 0.6
    }
  });

  /* =====================================================
     📍 LOCATIONS
  ===================================================== */
  // CONFIG: Auto-switch based on hostname
  // If running locally (localhost), use local backend using .env or defaults
  // If running on GitHub Pages, use your PROD backend URL
  const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

  // REPLACE 'https://your-render-app.onrender.com' WITH YOUR ACTUAL RENDER URL!
  const BACKEND_URL = isLocal ? "http://127.0.0.1:8000" : "https://west-hyderabad-intelligence.onrender.com";

  const res = await fetch(`${BACKEND_URL}/api/v1/insights`);
  const data = await res.json();

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

  map.addLayer({
    id: "location-core",
    type: "circle",
    source: "locations",
    paint: {
      "circle-radius": 12,
      "circle-color": "#2735d1",
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 2
    }
  });

  /* =====================================================
     LAYER TOGGLE (ONLY CHANGE)
  ===================================================== */
  document.querySelectorAll(".layer-tile input").forEach(cb => {
    cb.onchange = e => {
      const id = e.target.dataset.layer;
      if (map.getLayer(id)) {
        map.setLayoutProperty(
          id,
          "visibility",
          e.target.checked ? "visible" : "none"
        );
      }
    };
  });

  /* =====================================================
     CLICK → INTEL CARD
  ===================================================== */
  map.on("click", "location-core", e => {
    const p = e.features[0].properties;
    const card = document.getElementById("intel-card");
    const title = document.getElementById("app-title");

    title.style.visibility = "hidden";
    card.style.display = "flex";

    map.easeTo({
      center: [p.longitude, p.latitude],
      zoom: 13,
      duration: 800
    });

    const imageName = p.location.toLowerCase().replace(/\s+/g, "_");
    const imagePath = `assets/locations/${imageName}.jpg`;

    card.innerHTML = `

       
       <div class="location-image">
         <img src="${imagePath}" alt="${p.location}" onerror="this.src='assets/locations/default.jpg'" style="object-fit:cover; width:100%; height:100%;" />
       </div>

       <div class="intel-scroll-container">
          <h3>${p.location}</h3>
          <p class="location-subtitle">Real Estate Intelligence</p>

          <div class="metrics">
            <div class="metric-box">
              <span>Market Sentiment</span>
              <strong style="color:#60a5fa">${sentimentText(p.avg_sentiment)}</strong>
            </div>
    
            <div class="metric-box">
              <span>Growth Outlook</span>
              <strong style="color:#4ade80">${growthText(p.growth_score)}</strong>
            </div>
    
            <div class="metric-box">
              <span>Investment Score</span>
              <strong style="color:#facc15">${investmentText(p.investment_score)}</strong>
            </div>
          </div>

          <div class="card-actions" style="margin-top:32px;">
            <button id="download-report" style="width:100%; padding:14px; background:#2563eb; color:white; font-weight:bold; border:none; border-radius:12px; font-size:1rem;">Download PDF Report</button>
          </div>
       </div>
     `;

    document.getElementById("download-report").onclick =
      () => generateReport(p);



    if (activeMarker) activeMarker.remove();
    activeMarker = new maplibregl.Marker({ color: "#2563eb" })
      .setLngLat([p.longitude, p.latitude])
      .addTo(map);
  });

  map.on("click", e => {
    if (!map.queryRenderedFeatures(e.point, { layers: ["location-core"] }).length) {
      document.getElementById("app-title").style.visibility = "visible";
      document.getElementById("intel-card").style.display = "none";
      if (activeMarker) activeMarker.remove();
    }
  });
});
