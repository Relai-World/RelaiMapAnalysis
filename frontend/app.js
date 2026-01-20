const map = new maplibregl.Map({
  container: "map",
  style: "./style.json",
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
     🏫 SCHOOLS
  ===================================================== */
  map.loadImage(
  "./assets/schools.png",
    (error, image) => {
      if (error) throw error;

      if (!map.hasImage("school-icon")) {
        map.addImage("school-icon", image);
      }

      map.addSource("schools", {
        type: "vector",
        tiles: ["http://localhost:8080/data/schools/{z}/{x}/{y}.pbf"],
        minzoom: 6,
        maxzoom: 14
      });

      map.addLayer({
        id: "schools-layer",
        type: "symbol",
        source: "schools",
        "source-layer": "schools",
        layout: {
          "icon-image": "school-icon",
          "icon-size": ["interpolate", ["linear"], ["zoom"], 8, 0.03, 18, 0.06],
          "icon-allow-overlap": true,
          "icon-ignore-placement": true,
          "visibility": "none"
        }
      });
    }
  );

  /* =====================================================
     🛣️ HIGHWAYS
  ===================================================== */
  map.addSource("highways", {
    type: "vector",
    tiles: ["http://localhost:8080/data/highways/{z}/{x}/{y}.pbf"],
    minzoom: 6,
    maxzoom: 10
  });

  map.addLayer({
    id: "highways-layer",
    type: "line",
    source: "highways",
    "source-layer": "highways",
    layout: { visibility: "none", "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color":"#FF8700",
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.2, 18, 5.2],
      "line-opacity": 0.9
    }
  });

  /* =====================================================
     🚇 METRO
  ===================================================== */
  map.addSource("metro", {
    type: "vector",
    tiles: ["http://localhost:8080/data/metro/{z}/{x}/{y}.pbf"],
    minzoom: 6,
    maxzoom: 10
  });

  map.addLayer({
    id: "metro-layer",
    type: "line",
    source: "metro",
    "source-layer": "metro",
    layout: { visibility: "none", "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#ef0000",
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.2, 18, 4.8],
      "line-opacity": 0.95
    }
  });

  /* =====================================================
     🛣️ ORR
  ===================================================== */
  map.addSource("orr", {
    type: "vector",
    tiles: ["http://localhost:8080/data/orr/{z}/{x}/{y}.pbf"],
    minzoom: 6,
    maxzoom: 10
  });

  map.addLayer({
    id: "orr-layer",
    type: "line",
    source: "orr",
    "source-layer": "orr",
    layout: { visibility: "none", "line-join": "round", "line-cap": "round" },
    paint: {
      "line-color": "#070707ff",
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 1.5, 18, 6],
      "line-opacity": 0.95
    }
  });

  /* =====================================================
     🌊 LAKES
  ===================================================== */
  map.addSource("lakes", {
    type: "vector",
    tiles: ["http://localhost:8080/data/lakes/{z}/{x}/{y}.pbf"],
    minzoom: 6,
    maxzoom: 10
  });

  map.addLayer({
    id: "lakes-layer",
    type: "fill",
    source: "lakes",
    "source-layer": "lakes",
    layout: { visibility: "none" },
    paint: {
      "fill-color": "#38bdf8",
      "fill-opacity": 1.0,
      "fill-outline-color": "#0284c7"
    }
  });

  /* =====================================================
     📍 LOCATIONS
  ===================================================== */
  const res = await fetch("http://127.0.0.1:8000/api/v1/insights");
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
      "circle-radius": 6,
      "circle-color":"#2563eb", 
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
    card.style.display = "block";

    map.easeTo({
      center: [p.longitude, p.latitude],
      zoom: 13,
      duration: 800
    });

    const imageName = p.location.toLowerCase().replace(/\s+/g, "_");
    const imagePath = `assets/locations/${imageName}.jpg`;

    card.innerHTML = `
      <div class="location-image">
        <img src="${imagePath}" alt="${p.location}" onerror="this.style.display='none'" />
      </div>

      <p>${p.location}</p>

      <div class="metrics">
        <div class="metric-box">
          <span>Market Sentiment</span>
          <strong>${sentimentText(p.avg_sentiment)}</strong>
        </div>

        <div class="metric-box">
          <span>Growth Outlook</span>
          <strong>${growthText(p.growth_score)}</strong>
        </div>

        <div class="metric-box">
          <span>Investment Score</span>
          <strong>${investmentText(p.investment_score)}</strong>
        </div>
      </div>

      <div class="card-actions">
        <button id="download-report">Download Report</button>
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
