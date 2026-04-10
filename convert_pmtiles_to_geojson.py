#!/usr/bin/env python3
"""Convert PMTiles to GeoJSON for Bangalore floods layer"""

import json
from pmtiles.reader import Reader, MmapSource

def convert_pmtiles_to_geojson(pmtiles_path, output_path):
    """Extract features from PMTiles and save as GeoJSON"""
    
    print(f"Reading PMTiles from: {pmtiles_path}")
    
    # Open the PMTiles file
    with open(pmtiles_path, 'rb') as f:
        source = MmapSource(f)
        reader = Reader(source)
        
        # Get metadata
        metadata = reader.metadata()
        print(f"Metadata: {metadata}")
        
        # Get header info
        header = reader.header()
        print(f"Min zoom: {header['min_zoom']}, Max zoom: {header['max_zoom']}")
        print(f"Center: {header.get('center_lon', 'N/A')}, {header.get('center_lat', 'N/A')}")
        
        # For now, just print the structure
        # Full extraction would require iterating through tiles
        print("\nNote: Full GeoJSON extraction from PMTiles requires tile iteration")
        print("The PMTiles file is ready to use directly in MapLibre GL JS")

if __name__ == "__main__":
    pmtiles_path = "frontend/maptiles/bangalore_water_accumulation.pmtiles"
    output_path = "frontend/data/bangalore_floods.geojson"
    
    convert_pmtiles_to_geojson(pmtiles_path, output_path)
