#!/bin/bash

# Convert KML to GeoJSON
echo "🔄 Converting KML to GeoJSON..."

INPUT_KML="frontend/data/e56d21e8-0c44-4c35-9e5d-c732f6f59c97.kml"
OUTPUT_GEOJSON="frontend/data/converted_from_kml.geojson"

# Check if ogr2ogr is available
if ! command -v ogr2ogr &> /dev/null; then
    echo "❌ ogr2ogr not found. Please install GDAL:"
    echo "   Ubuntu/Debian: sudo apt-get install gdal-bin"
    echo "   macOS: brew install gdal"
    echo "   Windows: Install OSGeo4W or use WSL"
    exit 1
fi

# Convert KML to GeoJSON
ogr2ogr -f GeoJSON "$OUTPUT_GEOJSON" "$INPUT_KML"

if [ $? -eq 0 ]; then
    echo "✅ Conversion successful!"
    echo "📄 Output: $OUTPUT_GEOJSON"
    ls -lh "$OUTPUT_GEOJSON"
else
    echo "❌ Conversion failed"
    exit 1
fi
