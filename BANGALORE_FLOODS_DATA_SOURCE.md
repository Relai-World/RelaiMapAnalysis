# Bangalore Floods/Water Accumulation Data Source

## Repository Found
**GitHub**: [diagram-chasing/blr-water-log](https://github.com/diagram-chasing/blr-water-log)

**Description**: An interactive tool to explore water accumulation patterns around Bangalore, India.

**Live Demo**: https://diagramchasing.fun/2024/blr-water-log

## Key Findings

### 1. Data Files Available
Located in `static/` folder:
- **tiles.pmtiles** - Water accumulation/stream influence data in PMTiles format
- **basemap.pmtiles** - Basemap tiles for Bangalore

### 2. Data Generation Process
The repository includes scripts to generate water accumulation data from DEM (Digital Elevation Model):

**Location**: `data/dem/tiles.py`

**Process**:
1. Uses Copernicus GLO-30 DEM data
2. Calculates flow direction and flow accumulation
3. Extracts stream networks
4. Calculates stream influence areas (water accumulation zones)
5. Classifies into 4 levels of water accumulation risk
6. Converts to vector format (shapefile/GeoJSON)
7. Converts to PMTiles for web mapping

**Output Files Generated**:
- `stream_influence.tif` - Raster of water influence areas
- `stream_influence_reclass.tif` - Reclassified into 4 risk levels
- `stream_influence_reclass.shp` - Vector shapefile
- `tiles.pmtiles` - Final PMTiles for web use

### 3. Data Characteristics
- **Type**: Water accumulation/drainage patterns
- **Format**: PMTiles (vector tiles)
- **Classification**: 4 levels of water accumulation risk
- **Coverage**: Bangalore metropolitan area
- **Source**: Derived from Copernicus GLO-30 DEM

## How to Use This Data

### Option 1: Download PMTiles File
Download the pre-generated PMTiles file:
```
https://raw.githubusercontent.com/diagram-chasing/blr-water-log/master/static/tiles.pmtiles
```

### Option 2: Generate Your Own Data
Follow the repository's process:

1. Clone the repository
2. Navigate to `data/dem/`
3. Run `fetch.sh` to download DEM data
4. Run `tiles.py` to generate water accumulation data
5. Convert to PMTiles using scripts in `data/water-tile-generation/`

## Integration with Your App

### Current Bangalore Floods Layer
Your current `bangalore_floods.geojson` is a simple flood-prone areas layer.

### Enhanced Option with PMTiles
You can replace or supplement it with the water accumulation PMTiles:

```javascript
// Add water accumulation source
map.addSource("blr-water-accumulation-source", {
  type: "vector",
  url: "pmtiles://path/to/tiles.pmtiles",
  minzoom: 0,
  maxzoom: 14
});

// Add layer with 4 risk levels
map.addLayer({
  id: "blr-water-accumulation-layer",
  type: "fill",
  source: "blr-water-accumulation-source",
  "source-layer": "stream_influence", // Check actual layer name
  paint: {
    "fill-color": [
      "match",
      ["get", "class"], // Assuming 'class' property with values 1-4
      1, "#A5D8F3", // Low risk - Light blue
      2, "#4FC3F7", // Moderate risk - Medium blue
      3, "#0288D1", // High risk - Dark blue
      4, "#01579B", // Very high risk - Very dark blue
      "#cccccc"     // Default
    ],
    "fill-opacity": 0.6
  }
});
```

## Comparison with Current Data

### Current: `bangalore_floods.geojson`
- Simple polygon-based flood zones
- Binary (flood/no flood)
- Static data

### Enhanced: PMTiles from blr-water-log
- Scientifically derived from DEM analysis
- 4 levels of water accumulation risk
- Shows drainage patterns and flow paths
- More detailed and accurate
- Optimized for web (PMTiles format)

## Recommendations

### Short Term
Keep using your current `bangalore_floods.geojson` as it's already integrated.

### Medium Term
1. Download the `tiles.pmtiles` file from the repository
2. Host it in your `frontend/maptiles/` directory
3. Add it as an additional layer (not replacement)
4. Label it as "Water Accumulation Risk" or "Drainage Patterns"

### Long Term
Consider generating your own custom water accumulation data:
1. Use the repository's scripts
2. Customize the risk classification
3. Combine with local flood incident data
4. Update periodically with new DEM data

## Technical Details

### PMTiles Format
- Efficient vector tile format
- Single file (no tile server needed)
- Supports zoom levels
- Works with MapLibre GL JS

### Data Quality
- Based on Copernicus GLO-30 DEM (30m resolution)
- Scientifically validated approach
- Used in production by Diagram Chasing

### License
- Repository: MIT License
- DEM Data: Copernicus (free and open)

## Next Steps

1. **Download the PMTiles file**:
   ```bash
   curl -o frontend/maptiles/bangalore_water_accumulation.pmtiles \
     https://raw.githubusercontent.com/diagram-chasing/blr-water-log/master/static/tiles.pmtiles
   ```

2. **Inspect the PMTiles** to understand the data structure:
   - Use PMTiles viewer: https://protomaps.github.io/PMTiles/
   - Check layer names and properties

3. **Integrate into your app** following the code example above

4. **Test and compare** with your existing flood layer

## Resources

- **Repository**: https://github.com/diagram-chasing/blr-water-log
- **Live Demo**: https://diagramchasing.fun/2024/blr-water-log
- **PMTiles Spec**: https://github.com/protomaps/PMTiles
- **Copernicus DEM**: https://spacedata.copernicus.eu/

## Summary

The `diagram-chasing/blr-water-log` repository provides scientifically-derived water accumulation data for Bangalore that would be a significant upgrade over simple flood zone polygons. The data is available as PMTiles, making it easy to integrate into your MapLibre-based application.

The water accumulation layer shows 4 levels of risk based on terrain analysis, providing much more nuanced information about where water tends to accumulate during heavy rainfall.
