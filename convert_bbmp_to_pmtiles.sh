#!/bin/bash

# Convert Bangalore BBMP Boundary to PMTiles

echo "🗺️  Converting Bangalore BBMP Boundary to PMTiles..."

# Check if tippecanoe is installed
if ! command -v tippecanoe &> /dev/null; then
    echo "❌ Error: tippecanoe is not installed"
    echo "Install it using:"
    echo "  - macOS: brew install tippecanoe"
    echo "  - Ubuntu/WSL: sudo apt-get install tippecanoe"
    exit 1
fi

# Convert to PMTiles
tippecanoe -o frontend/maptiles/bangalore_bbmp.pmtiles \
  -Z0 -z14 \
  --drop-densest-as-needed \
  --extend-zooms-if-still-dropping \
  --force \
  frontend/data/Bangalore_bbmp1.geojson

if [ $? -eq 0 ]; then
    echo "✅ Bangalore BBMP converted successfully"
    echo ""
    echo "📊 File size:"
    ls -lh frontend/maptiles/bangalore_bbmp.pmtiles
else
    echo "❌ Failed to convert Bangalore BBMP"
    exit 1
fi
