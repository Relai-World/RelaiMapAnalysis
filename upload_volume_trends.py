#!/usr/bin/env python3
"""
Upload volume trends data to Supabase and integrate with the application
"""

import os
import csv
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def call_supabase_rpc(function_name, params=None):
    """Call a Supabase RPC function"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise Exception("Missing Supabase credentials in .env file")
    
    url = f"{supabase_url}/rest/v1/rpc/{function_name}"
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    body = params if params else {}
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code != 200:
        error_text = response.text
        raise Exception(f"Supabase RPC error: {response.status_code} - {error_text}")
    
    return response.json()

def insert_to_supabase_table(table_name, data):
    """Insert data directly to a Supabase table"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise Exception("Missing Supabase credentials in .env file")
    
    url = f"{supabase_url}/rest/v1/{table_name}"
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        error_text = response.text
        raise Exception(f"Supabase insert error: {response.status_code} - {error_text}")
    
    return True

def read_volume_trends_csv():
    """Read and parse the volume trends CSV file"""
    volume_data = []
    
    try:
        with open('final_realistic_dataset.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                location_name = row['Location']
                cluster = row['Cluster']
                
                # Create volume trend data for each year
                volume_record = {
                    'location_name': location_name,
                    'cluster': cluster,
                    'year_2018': int(row['2018']),
                    'year_2019': int(row['2019']),
                    'year_2020': int(row['2020']),
                    'year_2021': int(row['2021']),
                    'year_2022': int(row['2022']),
                    'year_2023': int(row['2023']),
                    'year_2024': int(row['2024']),
                    'year_2025': int(row['2025']),
                    'year_2026': int(row['2026'])
                }
                
                volume_data.append(volume_record)
        
        print(f"📊 Parsed {len(volume_data)} volume trend records")
        return volume_data
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return []

def create_volume_trends_table_sql():
    """Generate SQL to create the volume trends table"""
    sql = """
-- Create volume_trends table
CREATE TABLE IF NOT EXISTS volume_trends (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL,
    cluster VARCHAR(100),
    year_2018 INTEGER,
    year_2019 INTEGER,
    year_2020 INTEGER,
    year_2021 INTEGER,
    year_2022 INTEGER,
    year_2023 INTEGER,
    year_2024 INTEGER,
    year_2025 INTEGER,
    year_2026 INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(location_name)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_volume_trends_location ON volume_trends(location_name);

-- Create RPC function to get volume trends by location
CREATE OR REPLACE FUNCTION get_volume_trends_func(area_name TEXT)
RETURNS TABLE(
    location_name TEXT,
    cluster TEXT,
    year_2018 INTEGER,
    year_2019 INTEGER,
    year_2020 INTEGER,
    year_2021 INTEGER,
    year_2022 INTEGER,
    year_2023 INTEGER,
    year_2024 INTEGER,
    year_2025 INTEGER,
    year_2026 INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vt.location_name::TEXT,
        vt.cluster::TEXT,
        vt.year_2018,
        vt.year_2019,
        vt.year_2020,
        vt.year_2021,
        vt.year_2022,
        vt.year_2023,
        vt.year_2024,
        vt.year_2025,
        vt.year_2026
    FROM volume_trends vt
    WHERE LOWER(vt.location_name) = LOWER(area_name);
END;
$$ LANGUAGE plpgsql;
"""
    return sql

def upload_volume_trends():
    """Main function to upload volume trends data"""
    try:
        print("🚀 Starting volume trends upload process...")
        
        # Read CSV data
        volume_data = read_volume_trends_csv()
        
        if not volume_data:
            print("❌ No volume data to upload")
            return
        
        # Generate SQL for table creation
        sql_script = create_volume_trends_table_sql()
        
        # Save SQL script to file
        with open('create_volume_trends_table.sql', 'w', encoding='utf-8') as f:
            f.write(sql_script)
        
        print("✅ SQL script saved to 'create_volume_trends_table.sql'")
        print("📝 Please run this SQL script in your Supabase SQL editor first!")
        
        # Try to upload data (this will work after the table is created)
        print("\n🔄 Attempting to upload volume trends data...")
        
        try:
            # Upload in batches to avoid timeout
            batch_size = 50
            total_batches = (len(volume_data) + batch_size - 1) // batch_size
            
            for i in range(0, len(volume_data), batch_size):
                batch = volume_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                print(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} records)...")
                
                insert_to_supabase_table('volume_trends', batch)
                
                print(f"✅ Batch {batch_num} uploaded successfully")
            
            print(f"\n🎉 Successfully uploaded {len(volume_data)} volume trend records!")
            
        except Exception as upload_error:
            print(f"⚠️ Upload failed: {upload_error}")
            print("This is expected if the table doesn't exist yet.")
            print("Please run the SQL script first, then run this script again.")
        
        # Generate sample frontend integration code
        generate_frontend_integration_code()
        
    except Exception as e:
        print(f"❌ Error in upload process: {e}")

def generate_frontend_integration_code():
    """Generate sample code for frontend integration"""
    
    frontend_code = '''
// Add this to your frontend/app.js file

// Function to fetch volume trends for a location
async function fetchVolumeTrends(locationName) {
  try {
    console.log(`🔍 Fetching volume trends for: ${locationName}`);
    
    const volumeData = await callSupabaseRPC('get_volume_trends_func', { 
      area_name: locationName 
    });
    
    if (volumeData && volumeData.length > 0) {
      return volumeData[0]; // Return first match
    }
    
    return null;
  } catch (error) {
    console.error('❌ Error fetching volume trends:', error);
    return null;
  }
}

// Function to draw volume trends chart
function drawVolumeTrendsChart(volumeData, locationName) {
  const chartContainer = document.getElementById('volume-trends-chart');
  
  if (!volumeData || !chartContainer) {
    console.log('No volume data or chart container found');
    return;
  }
  
  // Prepare data for Chart.js
  const years = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026'];
  const volumes = [
    volumeData.year_2018,
    volumeData.year_2019,
    volumeData.year_2020,
    volumeData.year_2021,
    volumeData.year_2022,
    volumeData.year_2023,
    volumeData.year_2024,
    volumeData.year_2025,
    volumeData.year_2026
  ];
  
  // Create chart
  const ctx = chartContainer.getContext('2d');
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: years,
      datasets: [{
        label: 'Transaction Volume',
        data: volumes,
        borderColor: '#10B981', // Green color
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Volume Trends - ${locationName}`,
          font: { size: 16, weight: 'bold' }
        },
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of Transactions'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Year'
          }
        }
      }
    }
  });
}

// Update your existing showLocationDetails function to include volume trends
// Add this after the price trends chart:

async function showLocationDetailsWithVolume(locationName, locationId) {
  // ... existing code for price trends ...
  
  // Add volume trends
  const volumeData = await fetchVolumeTrends(locationName);
  
  if (volumeData) {
    // Add volume trends section to your modal
    const volumeSection = `
      <div class="volume-trends-section" style="margin-top: 20px;">
        <h4>📊 Transaction Volume Trends</h4>
        <p><strong>Market Cluster:</strong> ${volumeData.cluster}</p>
        <canvas id="volume-trends-chart" width="400" height="200"></canvas>
      </div>
    `;
    
    // Append to your existing modal content
    // Then call drawVolumeTrendsChart(volumeData, locationName);
  }
}
'''
    
    # Save frontend integration code
    with open('volume_trends_frontend_integration.js', 'w', encoding='utf-8') as f:
        f.write(frontend_code)
    
    print("✅ Frontend integration code saved to 'volume_trends_frontend_integration.js'")

if __name__ == "__main__":
    upload_volume_trends()