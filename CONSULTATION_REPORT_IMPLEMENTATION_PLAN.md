# Consultation Report - Implementation Plan

## What You Need

A comprehensive PDF report for expert consultation sessions that includes:

✅ **Property Comparison** (already implemented)
🔲 **Map Screenshots** with layers and amenities visible
🔲 **Session Summary** (locations explored, properties viewed)
🔲 **Location Insights** for areas of interest
🔲 **Expert Recommendations** section

## Recommended Approach

### Solution: Multi-Section PDF Report

**Architecture**:
```
Session Tracker → Data Collector → Report Builder → PDF Generator
```

**Key Components**:
1. **Session Tracker**: Tracks user interactions during consultation
2. **Map Screenshot**: Captures current map view with layers
3. **Report Builder**: Assembles all sections into HTML
4. **PDF Generator**: Uses html2pdf to create final document

## Implementation Steps

### Step 1: Session Tracking (2 hours)

Create `frontend/consultation-session.js`:

```javascript
class ConsultationSession {
  constructor() {
    this.sessionId = Date.now();
    this.startTime = new Date();
    this.clientName = '';
    this.expertName = '';
    
    // Track interactions
    this.locationsViewed = new Map(); // areaName -> {timestamp, viewCount}
    this.propertiesViewed = new Map(); // propertyId -> {name, timestamp}
    this.propertiesCompared = []; // Array of property objects
    this.mapStates = []; // Array of {screenshot, layers, timestamp}
    this.expertNotes = '';
  }
  
  // Track when user clicks on a location
  trackLocationView(areaName) {
    if (!this.locationsViewed.has(areaName)) {
      this.locationsViewed.set(areaName, {
        timestamp: new Date(),
        viewCount: 1
      });
    } else {
      const data = this.locationsViewed.get(areaName);
      data.viewCount++;
    }
  }
  
  // Track when user views property details
  trackPropertyView(property) {
    this.propertiesViewed.set(property.id, {
      name: property.projectname,
      area: property.areaname,
      timestamp: new Date()
    });
  }
  
  // Track properties being compared
  setComparedProperties(properties) {
    this.propertiesCompared = properties;
  }
  
  // Capture current map state
  async captureMapState(map, activeLayers) {
    const canvas = map.getCanvas();
    const screenshot = canvas.toDataURL('image/png', 1.0);
    
    this.mapStates.push({
      screenshot: screenshot,
      layers: [...activeLayers],
      center: map.getCenter(),
      zoom: map.getZoom(),
      timestamp: new Date()
    });
  }
  
  // Get session summary
  getSummary() {
    return {
      sessionId: this.sessionId,
      duration: new Date() - this.startTime,
      locationsCount: this.locationsViewed.size,
      propertiesViewedCount: this.propertiesViewed.size,
      propertiesComparedCount: this.propertiesCompared.length,
      mapScreenshotsCount: this.mapStates.length
    };
  }
}

// Global session instance
window.consultationSession = new ConsultationSession();
```

### Step 2: Map Screenshot Capture (1 hour)

Add to `frontend/app.js`:

```javascript
// Function to capture current map view
async function captureMapScreenshot() {
  const activeLayers = cityLayerManager.getActiveLayers(); // Get from city-layers.js
  await consultationSession.captureMapState(map, activeLayers);
  showNotification('Map view captured!', 'success');
}

// Add button to UI
<button onclick="captureMapScreenshot()" class="capture-map-btn">
  📸 Capture Map View
</button>
```

### Step 3: Report Builder (4 hours)

Create `frontend/consultation-report-builder.js`:

```javascript
class ConsultationReportBuilder {
  constructor(session, locationInsights) {
    this.session = session;
    this.locationInsights = locationInsights;
  }
  
  buildCoverPage() {
    const summary = this.session.getSummary();
    return `
      <div class="report-page cover-page">
        <div class="report-header">
          <h1>Property Consultation Report</h1>
          <div class="report-meta">
            <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
            <p><strong>Client:</strong> ${this.session.clientName || 'N/A'}</p>
            <p><strong>Consultant:</strong> ${this.session.expertName || 'N/A'}</p>
          </div>
        </div>
        
        <div class="session-summary">
          <h2>Session Summary</h2>
          <div class="summary-stats">
            <div class="stat-card">
              <div class="stat-number">${summary.locationsCount}</div>
              <div class="stat-label">Locations Explored</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">${summary.propertiesViewedCount}</div>
              <div class="stat-label">Properties Viewed</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">${summary.propertiesComparedCount}</div>
              <div class="stat-label">Properties Compared</div>
            </div>
          </div>
          
          <h3>Locations of Interest</h3>
          <ul class="locations-list">
            ${Array.from(this.session.locationsViewed.entries())
              .map(([name, data]) => `<li>${name} (viewed ${data.viewCount} times)</li>`)
              .join('')}
          </ul>
        </div>
      </div>
    `;
  }
  
  buildMapSection() {
    if (this.session.mapStates.length === 0) {
      return '';
    }
    
    return this.session.mapStates.map((state, index) => `
      <div class="report-page map-page">
        <h2>Map View ${index + 1}</h2>
        <div class="map-info">
          <p><strong>Captured:</strong> ${state.timestamp.toLocaleString()}</p>
          <p><strong>Active Layers:</strong> ${state.layers.join(', ') || 'None'}</p>
        </div>
        <img src="${state.screenshot}" class="map-screenshot" alt="Map view ${index + 1}" />
      </div>
    `).join('');
  }
  
  buildComparisonSection() {
    if (this.session.propertiesCompared.length === 0) {
      return '';
    }
    
    // Clone the existing comparison table
    const comparisonTable = document.querySelector('.comparison-table-container');
    if (!comparisonTable) {
      return '<div class="report-page"><p>No comparison data available</p></div>';
    }
    
    const clone = comparisonTable.cloneNode(true);
    
    // Remove UI buttons
    clone.querySelectorAll('.remove-property-btn').forEach(btn => btn.remove());
    clone.querySelectorAll('.export-btn').forEach(btn => btn.remove());
    
    return `
      <div class="report-page comparison-page">
        <h2>Property Comparison</h2>
        ${clone.outerHTML}
      </div>
    `;
  }
  
  buildLocationInsights() {
    const locations = Array.from(this.session.locationsViewed.keys());
    
    if (locations.length === 0) {
      return '';
    }
    
    return `
      <div class="report-page insights-page">
        <h2>Location Insights</h2>
        ${locations.map(areaName => {
          const insight = this.locationInsights.get(areaName.toLowerCase());
          
          if (!insight) {
            return `
              <div class="location-insight-card">
                <h3>${areaName}</h3>
                <p><em>No detailed insights available</em></p>
              </div>
            `;
          }
          
          return `
            <div class="location-insight-card">
              <h3>${areaName}</h3>
              <div class="grid-scores">
                <div class="score-item">
                  <span class="score-label">Connectivity</span>
                  <span class="score-value">${(insight.connectivity_score || 0).toFixed(1)}/10</span>
                </div>
                <div class="score-item">
                  <span class="score-label">Amenities</span>
                  <span class="score-value">${(insight.amenities_score || 0).toFixed(1)}/10</span>
                </div>
                <div class="score-item">
                  <span class="score-label">Growth</span>
                  <span class="score-value">${((insight.growth_score || 0) * 10).toFixed(1)}/10</span>
                </div>
                <div class="score-item">
                  <span class="score-label">Investment</span>
                  <span class="score-value">${((insight.investment_score || 0) * 10).toFixed(1)}/10</span>
                </div>
              </div>
              
              ${insight.key_highlights ? `
                <div class="highlights">
                  <h4>Key Highlights</h4>
                  <p>${insight.key_highlights}</p>
                </div>
              ` : ''}
              
              ${insight.concerns ? `
                <div class="concerns">
                  <h4>Concerns</h4>
                  <p>${insight.concerns}</p>
                </div>
              ` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  }
  
  buildRecommendations() {
    if (!this.session.expertNotes || this.session.expertNotes.trim() === '') {
      return '';
    }
    
    return `
      <div class="report-page recommendations-page">
        <h2>Expert Recommendations</h2>
        <div class="expert-notes">
          ${this.session.expertNotes.split('\n').map(line => `<p>${line}</p>`).join('')}
        </div>
        
        <div class="next-steps">
          <h3>Next Steps</h3>
          <ol>
            <li>Schedule site visits for shortlisted properties</li>
            <li>Verify RERA registration and builder credentials</li>
            <li>Review legal documents with property lawyer</li>
            <li>Finalize financing options</li>
          </ol>
        </div>
        
        <div class="contact-info">
          <h3>Follow-up</h3>
          <p>For questions or additional information, please contact your consultant.</p>
        </div>
      </div>
    `;
  }
  
  buildFullReport() {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>Consultation Report</title>
        <style>
          ${this.getReportStyles()}
        </style>
      </head>
      <body>
        <div class="consultation-report">
          ${this.buildCoverPage()}
          ${this.buildMapSection()}
          ${this.buildComparisonSection()}
          ${this.buildLocationInsights()}
          ${this.buildRecommendations()}
        </div>
      </body>
      </html>
    `;
  }
  
  getReportStyles() {
    return `
      * { margin: 0; padding: 0; box-sizing: border-box; }
      
      body {
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #333;
        background: white;
        line-height: 1.6;
      }
      
      .consultation-report {
        max-width: 210mm;
        margin: 0 auto;
      }
      
      .report-page {
        page-break-after: always;
        padding: 20mm;
        min-height: 297mm;
      }
      
      .report-header {
        border-bottom: 3px solid #3350c0;
        padding-bottom: 15px;
        margin-bottom: 30px;
      }
      
      .report-header h1 {
        color: #3350c0;
        font-size: 32px;
        margin-bottom: 15px;
      }
      
      .report-meta p {
        margin: 5px 0;
        font-size: 14px;
      }
      
      .session-summary {
        margin-top: 30px;
      }
      
      .summary-stats {
        display: flex;
        gap: 20px;
        margin: 20px 0;
      }
      
      .stat-card {
        flex: 1;
        background: #f3f4f6;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
      }
      
      .stat-number {
        font-size: 36px;
        font-weight: bold;
        color: #3350c0;
      }
      
      .stat-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
      }
      
      .locations-list {
        list-style-position: inside;
        margin: 15px 0;
      }
      
      .locations-list li {
        padding: 8px 0;
        border-bottom: 1px solid #e5e7eb;
      }
      
      .map-screenshot {
        width: 100%;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin: 20px 0;
      }
      
      .map-info {
        background: #f9fafb;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
      }
      
      .location-insight-card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        page-break-inside: avoid;
      }
      
      .location-insight-card h3 {
        color: #3350c0;
        margin-bottom: 15px;
      }
      
      .grid-scores {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin: 15px 0;
      }
      
      .score-item {
        text-align: center;
        padding: 10px;
        background: #f3f4f6;
        border-radius: 6px;
      }
      
      .score-label {
        display: block;
        font-size: 12px;
        color: #666;
        margin-bottom: 5px;
      }
      
      .score-value {
        display: block;
        font-size: 20px;
        font-weight: bold;
        color: #3350c0;
      }
      
      .highlights, .concerns {
        margin: 15px 0;
      }
      
      .highlights h4, .concerns h4 {
        font-size: 14px;
        margin-bottom: 8px;
        color: #555;
      }
      
      .expert-notes {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 20px;
        margin: 20px 0;
      }
      
      .next-steps ol {
        margin: 15px 0 15px 25px;
      }
      
      .next-steps li {
        padding: 8px 0;
      }
      
      .contact-info {
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
      }
      
      h2 {
        color: #3350c0;
        font-size: 24px;
        margin-bottom: 20px;
      }
      
      h3 {
        font-size: 18px;
        margin: 20px 0 10px 0;
      }
    `;
  }
  
  async generatePDF() {
    const reportHTML = this.buildFullReport();
    
    // Create temporary container
    const container = document.createElement('div');
    container.innerHTML = reportHTML;
    container.style.position = 'absolute';
    container.style.left = '-9999px';
    document.body.appendChild(container);
    
    const opt = {
      margin: 0,
      filename: `consultation-report-${this.session.sessionId}.pdf`,
      image: { type: 'jpeg', quality: 0.95 },
      html2canvas: { 
        scale: 2,
        useCORS: true,
        letterRendering: true
      },
      jsPDF: { 
        unit: 'mm', 
        format: 'a4', 
        orientation: 'portrait'
      },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };
    
    try {
      await html2pdf().set(opt).from(container).save();
      document.body.removeChild(container);
      return true;
    } catch (error) {
      console.error('PDF generation failed:', error);
      document.body.removeChild(container);
      return false;
    }
  }
}
```

### Step 4: UI Integration (1 hour)

Add to `frontend/comparison-ui.js`:

```javascript
// Add new button for consultation report
<button onclick="generateConsultationReport()" class="export-btn consultation-report-btn">
  📋 Generate Consultation Report
</button>

// Function to show modal and generate report
async function generateConsultationReport() {
  // Show modal to collect expert notes
  const modal = showReportOptionsModal();
  
  modal.onConfirm = async (options) => {
    consultationSession.clientName = options.clientName;
    consultationSession.expertName = options.expertName;
    consultationSession.expertNotes = options.expertNotes;
    
    // Set compared properties
    consultationSession.setComparedProperties(comparisonUI.properties);
    
    // Generate report
    const builder = new ConsultationReportBuilder(
      consultationSession,
      comparisonUI.locationInsights
    );
    
    showNotification('Generating consultation report...', 'info');
    
    const success = await builder.generatePDF();
    
    if (success) {
      showNotification('Consultation report generated successfully!', 'success');
    } else {
      showNotification('Failed to generate report', 'error');
    }
  };
}

function showReportOptionsModal() {
  // Create modal HTML
  const modalHTML = `
    <div class="modal-overlay" id="reportOptionsModal">
      <div class="modal-content">
        <h2>Generate Consultation Report</h2>
        
        <div class="form-group">
          <label>Client Name (optional)</label>
          <input type="text" id="clientName" placeholder="Enter client name">
        </div>
        
        <div class="form-group">
          <label>Expert/Consultant Name (optional)</label>
          <input type="text" id="expertName" placeholder="Enter your name">
        </div>
        
        <div class="form-group">
          <label>Expert Recommendations</label>
          <textarea id="expertNotes" rows="6" placeholder="Add your recommendations, observations, and next steps..."></textarea>
        </div>
        
        <div class="form-actions">
          <button onclick="closeReportModal()" class="btn-secondary">Cancel</button>
          <button onclick="confirmReportGeneration()" class="btn-primary">Generate Report</button>
        </div>
      </div>
    </div>
  `;
  
  // Add to page
  document.body.insertAdjacentHTML('beforeend', modalHTML);
  
  return {
    onConfirm: null
  };
}
```

### Step 5: Styling (1 hour)

Add to `frontend/style.css`:

```css
/* Consultation Report Styles */
.consultation-report-btn {
  background: #10b981;
  color: white;
  margin-left: 10px;
}

.consultation-report-btn:hover {
  background: #059669;
}

.capture-map-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background: white;
  border: 2px solid #3350c0;
  color: #3350c0;
  padding: 10px 15px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.capture-map-btn:hover {
  background: #3350c0;
  color: white;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 25px;
}

.btn-primary, .btn-secondary {
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary {
  background: #3350c0;
  color: white;
}

.btn-secondary {
  background: #e5e7eb;
  color: #333;
}
```

## Files to Create

1. `frontend/consultation-session.js` - Session tracking
2. `frontend/consultation-report-builder.js` - Report generation
3. Update `frontend/comparison-ui.js` - Add report button
4. Update `frontend/app.js` - Add map capture button
5. Update `frontend/style.css` - Add report styles
6. Update `frontend/index.html` - Import new scripts

## Testing Checklist

- [ ] Session tracks location views
- [ ] Session tracks property views
- [ ] Map screenshot captures correctly
- [ ] Report modal shows and collects data
- [ ] Cover page generates with correct data
- [ ] Map section shows screenshots
- [ ] Comparison section includes full table
- [ ] Location insights display correctly
- [ ] Expert recommendations appear
- [ ] PDF downloads successfully
- [ ] PDF is readable and well-formatted

## Estimated Timeline

- **Session Tracking**: 2 hours
- **Map Screenshot**: 1 hour
- **Report Builder**: 4 hours
- **UI Integration**: 1 hour
- **Styling**: 1 hour
- **Testing & Refinement**: 2 hours

**Total**: ~11 hours

## Next Steps

1. Review this plan
2. Confirm which sections are must-have
3. Start with Phase 1 (basic report)
4. Test with real consultation session
5. Iterate based on feedback
