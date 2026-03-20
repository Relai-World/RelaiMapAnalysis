#!/usr/bin/env python3
"""
Convert volume trends CSV to JavaScript format for direct frontend use
"""

import csv
import json

def convert_csv_to_js():
    """Convert CSV to JavaScript object format"""
    volume_data = {}
    
    try:
        with open('final_realistic_dataset.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                location_name = row['Location']
                
                # Create volume data object for each location
                volume_data[location_name] = {
                    'location_name': location_name,
                    'cluster': row['Cluster'],
                    'years': ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026'],
                    'volumes': [
                        int(row['2018']),
                        int(row['2019']),
                        int(row['2020']),
                        int(row['2021']),
                        int(row['2022']),
                        int(row['2023']),
                        int(row['2024']),
                        int(row['2025']),
                        int(row['2026'])
                    ]
                }
        
        print(f"📊 Converted {len(volume_data)} locations to JavaScript format")
        
        # Generate JavaScript file
        js_content = f"""// Volume trends data converted from CSV for direct frontend use
// Generated automatically - do not edit manually

const VOLUME_TRENDS_DATA = {json.dumps(volume_data, indent=2)};

// Helper function to get volume trends for a location
function getVolumeTrends(locationName) {{
  // Try exact match first
  if (VOLUME_TRENDS_DATA[locationName]) {{
    return VOLUME_TRENDS_DATA[locationName];
  }}
  
  // Try case-insensitive match
  const lowerLocationName = locationName.toLowerCase();
  for (const [key, value] of Object.entries(VOLUME_TRENDS_DATA)) {{
    if (key.toLowerCase() === lowerLocationName) {{
      return value;
    }}
  }}
  
  // Try partial match
  for (const [key, value] of Object.entries(VOLUME_TRENDS_DATA)) {{
    if (key.toLowerCase().includes(lowerLocationName) || 
        lowerLocationName.includes(key.toLowerCase())) {{
      return value;
    }}
  }}
  
  return null;
}}

// Get all available locations
function getAvailableVolumeLocations() {{
  return Object.keys(VOLUME_TRENDS_DATA);
}}

// Get cluster information
function getLocationCluster(locationName) {{
  const data = getVolumeTrends(locationName);
  return data ? data.cluster : null;
}}
"""
        
        # Write to JavaScript file
        with open('frontend/volume_trends_data.js', 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        print("✅ JavaScript file created: frontend/volume_trends_data.js")
        
        # Show sample data
        print("\n📋 Sample locations:")
        sample_locations = list(volume_data.keys())[:5]
        for loc in sample_locations:
            data = volume_data[loc]
            print(f"  - {loc} ({data['cluster']}): {data['volumes'][0]} → {data['volumes'][-1]} transactions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting CSV: {e}")
        return False

if __name__ == "__main__":
    convert_csv_to_js()