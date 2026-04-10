#!/bin/bash

# ============================================================
# Convert Bangalore GeoJSON files to PMTiles
# ============================================================

echo "🚀 Starting Bangalore GeoJSON → PMTiles conversion..."
echo ""

# Check if tippecanoe is installed
if ! command -v tippecanoe &> /dev/null; then
    echo "❌ Error: tippecanoe is not installed"
    echo "Install it using:"
    echo "  - macOS: brew install tippecanoe"
    echo "  - Ubuntu/WSL: sudo apt-get install tippecanoe"
    echo "  - Or use Docker: docker run -v $(pwd):/data felt/tippecanoe"
    exit 1
fi

# Create maptiles directory if it doesn't exist
mkdir -p maptiles

# Convert Bangalore Highways
echo "📍 Converting Bangalore Highways..."
tippecanoe -o maptiles/bangalore_highways.pmtiles \
  -Z0 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  frontend/data/banglore_highways.geojson

if [ $? -eq 0 ]; then
    echo "✅ Bangalore Highways converted successfully"
else
    echo "❌ Failed to convert Bangalore Highways"
fi
echo ""

# Convert Bangalore Metro
echo "🚇 Converting Bangalore Metro..."
tippecanoe -o maptiles/bangalore_metro.pmtiles \
  -Z0 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  frontend/data/metro-lines-stations.geojson

if [ $? -eq 0 ]; then
    echo "✅ Bangalore Metro converted successfully"
else
    echo "❌ Failed to convert Bangalore Metro"
fi
echo ""

# Convert Bangalore Lakes
echo "💧 Converting Bangalore Lakes..."
tippecanoe -o maptiles/bangalore_lakes.pmtiles \
  -Z0 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  frontend/data/bangalore_lakes.geojson

if [ $? -eq 0 ]; then
    echo "✅ Bangalore Lakes converted successfully"
else
    echo "❌ Failed to convert Bangalore Lakes"
fi
echo ""

# Convert Bangalore PRR
echo "🛣️  Converting Bangalore PRR..."
tippecanoe -o maptiles/bangalore_prr.pmtiles \
  -Z0 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  frontend/data/PRR.geojson

if [ $? -eq 0 ]; then
    echo "✅ Bangalore PRR converted successfully"
else
    echo "❌ Failed to convert Bangalore PRR"
fi
echo ""

# Convert Bangalore BBMP Boundary
echo "🗺️  Converting Bangalore BBMP Boundary..."
tippecanoe -o maptiles/bangalore_bbmp.pmtiles \
  -Z0 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  frontend/data/Bangalore_bbmp1.geojson

if [ $? -eq 0 ]; then
    echo "✅ Bangalore BBMP converted successfully"
else
    echo "❌ Failed to convert Bangalore BBMP"
fi
echo ""

echo "🎉 Conversion complete!"
echo ""
echo "📊 File sizes:"
ls -lh maptiles/bangalore_*.pmtiles 2>/dev/null || echo "No files found"
echo ""
echo "Next steps:"
echo "1. Run the app.js updates (already prepared)"
echo "2. Test the map to ensure all layers render correctly"
echo "3. Delete the old GeoJSON files from frontend/data/ (optional)"
