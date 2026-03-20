
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
